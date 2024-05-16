#!/usr/bin/python3
import cgi
import cgitb
import json
import pymysql
import csv
import sys

cgitb.enable()  # Enable detailed error reporting

# Function to establish database connection
def db_connect():
    try:
        return pymysql.connect(host="bioed.bu.edu", user="user", passwd="pwd", db="db", port=port)
    except pymysql.MySQLError as e:
        print("Content-type: text/html\n")
        print(f"<h1>Failed to connect to database:</h1><p>{str(e)}</p>")
        return None

# Function to count items based on conditions
def count_items(cursor, table_name, conditions, params):
    if conditions:
        query = f"SELECT COUNT(*) FROM {table_name} WHERE " + " AND ".join(conditions)
    else:
        query = f"SELECT COUNT(*) FROM {table_name}"
    cursor.execute(query, params)
    return cursor.fetchone()[0]

# Function to fetch data based on conditions, pagination, and offset
def fetch_data(cursor, table_name, conditions, params, items_per_page, offset, order):
    if conditions:
        query = f"SELECT TF, TG, Importance FROM {table_name} WHERE " + " AND ".join(conditions)
    else:
        query = f"SELECT TF, TG, Importance FROM {table_name}"
    query += f" ORDER BY Importance {order} LIMIT %s OFFSET %s"
    params.extend([items_per_page, offset])
    cursor.execute(query, params)
    results = cursor.fetchall()
    return [{'TF': row[0], 'TG': row[1], 'Importance': row[2]} for row in results]

# Function to handle data download
def handle_download(cursor, table_name, conditions, params, order):
    query = f"SELECT TF, TG, Importance FROM {table_name}"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += f" ORDER BY Importance {order}"
    cursor.execute(query, params)
    results = cursor.fetchall()
    
    # Clear any previous output:
    sys.stdout.flush()
    
    # Set the headers for a file download:
    print("Content-Type: text/csv")
    print("Content-Disposition: attachment; filename=download.csv")
    print()  # End of headers

    writer = csv.writer(sys.stdout, lineterminator='\n')  # Ensure correct line endings
    writer.writerow(['TF', 'TG', 'Importance'])
    for row in results:
        writer.writerow(row)
    
    # Make sure to flush the output at the end
    sys.stdout.flush()

# Main function to handle HTTP request and generate response
def main():
    form = cgi.FieldStorage()
    TF = form.getvalue('TF')
    TG = form.getvalue('TG')
    cell_type = form.getvalue('cell_type', 'Microglia')  # Default to 'Microglia' if not provided
    Importance = form.getvalue('Importance')
    order = form.getvalue('score_order', 'asc')  # Default order
    page = int(form.getvalue('page', 1))  # Default page
    items_per_page = 10
    offset = (page - 1) * items_per_page

    # Convert cell_type to corresponding table name
    table_name = f"{cell_type}"

    conn = db_connect()
    if conn:
        cursor = conn.cursor()
        conditions = []
        params = []
        if TF:
            conditions.append("TF = %s")
            params.append(TF)
        if TG:
            conditions.append("TG = %s")
            params.append(TG)
        if Importance is not None:
            conditions.append("Importance = %s")
            params.append(float(Importance))  # Assuming Importance is a float

        if 'download' in form:
            handle_download(cursor, table_name, conditions, params, order)
            cursor.close()
            conn.close()
            return  # End execution after handling download

        total_items = count_items(cursor, table_name, conditions, params)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        results = fetch_data(cursor, table_name, conditions, params, items_per_page, offset, order)

        output = {
            "tableData": results,
            "totalPages": total_pages,
        }
        print("Content-Type: application/json\n")  # MIME type plus newline for headers end
        print(json.dumps(output))
        cursor.close()
    else:
        print(json.dumps({"error": "Failed to connect to the database."}))

    if conn:
        conn.close()

if __name__ == "__main__":
    main()

