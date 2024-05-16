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
        return pymysql.connect(host="bioed.bu.edu", user="bkapalli", passwd="bkapalli", db="Team_10", port=4253)
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
        query = f"SELECT CRE_ID, Gene_ID, SNP_ID, Proximity_Score FROM {table_name} WHERE " + " AND ".join(conditions)
    else:
        query = f"SELECT CRE_ID, Gene_ID, SNP_ID, Proximity_Score FROM {table_name}"
    query += f" ORDER BY Proximity_Score {order} LIMIT %s OFFSET %s"
    params.extend([items_per_page, offset])
    cursor.execute(query, params)
    results = cursor.fetchall()
    return [{'CRE_ID': row[0], 'Gene_ID': row[1], 'SNP_ID': row[2], 'Proximity_Score': row[3]} for row in results]

# Function to handle data download
def handle_download(cursor, table_name, conditions, params, order):
    query = f"SELECT CRE_ID, Gene_ID, SNP_ID, Proximity_Score FROM {table_name}"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += f" ORDER BY Proximity_Score {order}"
    cursor.execute(query, params)
    results = cursor.fetchall()
    
    # Clear any previous output:
    sys.stdout.flush()
    
    # Set the headers for a file download:
    print("Content-Type: text/csv")
    print("Content-Disposition: attachment; filename=download.csv")
    print()  # End of headers

    writer = csv.writer(sys.stdout, lineterminator='\n')  # Ensure correct line endings
    writer.writerow(['CRE_ID', 'Gene_ID', 'SNP_ID', 'Proximity_Score'])
    for row in results:
        writer.writerow(row)
    
    # Make sure to flush the output at the end
    sys.stdout.flush()

# Main function to handle HTTP request and generate response
def main():
    form = cgi.FieldStorage()
    gene_id = form.getvalue('gene_id')
    cre_id = form.getvalue('cre_id')
    snp_id = form.getvalue('snp_id')
    cell_type = form.getvalue('cell_type', 'Astrocytes')  # Default to 'Astrocytes' if not provided
    proximity_score = form.getvalue('proximity_score')
    order = form.getvalue('score_order', 'asc')  # Default order
    page = int(form.getvalue('page', 1))  # Default page
    items_per_page = 20
    offset = (page - 1) * items_per_page

    # Convert cell_type to corresponding table name
    table_name = f"linked_{cell_type.replace(' ', '_').replace('/', '_or_')}_all_chromosomes"

    conn = db_connect()
    if conn:
        cursor = conn.cursor()
        conditions = []
        params = []
        if gene_id:
            conditions.append("Gene_ID = %s")
            params.append(gene_id)
        if cre_id:
            conditions.append("CRE_ID = %s")
            params.append(cre_id)
        if snp_id:
            conditions.append("SNP_ID = %s")
            params.append(snp_id)
        if proximity_score is not None:
            conditions.append("Proximity_Score = %s")
            params.append(float(proximity_score))  # Assuming proximity score is a float

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
            "heatmapData": results
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

