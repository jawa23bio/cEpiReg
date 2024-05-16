#!/usr/bin/env python3
import cgi
import cgitb
import json
import pymysql

cgitb.enable()  # Enable detailed error reporting

def db_connect():
    try:
        return pymysql.connect(host="bioed.bu.edu", user="bkapalli", passwd="bkapalli", db="Team_10", port=4253)
    except pymysql.MySQLError as e:
        print("Content-type: text/html\n")
        print(f"<h1>Failed to connect to database:</h1><p>{str(e)}</p>")
        return None

def count_items(cursor, table_name, conditions, params):
    if conditions:
        query = f"SELECT COUNT(*) FROM {table_name} WHERE " + " AND ".join(conditions)
    else:
        query = f"SELECT COUNT(*) FROM {table_name}"
    cursor.execute(query, params)
    return cursor.fetchone()[0]

def fetch_data(cursor, table_name, conditions, params, items_per_page, offset):
    if conditions:
        query = f"SELECT CRE_ID, Gene_ID, SNP_ID, Proximity_Score FROM {table_name} WHERE " + " AND ".join(conditions)
    else:
        query = f"SELECT CRE_ID, Gene_ID, SNP_ID, Proximity_Score FROM {table_name}"
    query += " LIMIT %s OFFSET %s"
    params.extend([items_per_page, offset])
    cursor.execute(query, params)
    results = cursor.fetchall()
    return [{'CRE_ID': row[0], 'Gene_ID': row[1], 'SNP_ID': row[2], 'Proximity_Score': row[3]} for row in results]

def main():
    print("Content-Type: application/json\n")  # MIME type plus newline for headers end

    form = cgi.FieldStorage()
    gene_id = form.getvalue('gene_id')
    cre_id = form.getvalue('cre_id')
    snp_id = form.getvalue('snp_id')
    cell_type = form.getvalue('cell_type', 'Astrocytes')  # Default to 'Astrocytes' if not provided
    proximity_score_min = form.getvalue('proximity_score_min')
    proximity_score_max = form.getvalue('proximity_score_max')
    page = int(form.getvalue('page', 1))  # Default page
    items_per_page = 10
    offset = (page - 1) * items_per_page

    # Convert cell_type to corresponding table name
    table_name = f"linked_{cell_type.replace(' ', '_').replace('/','_or_')}_all_chromosomes"

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
        if proximity_score_min is not None:
            conditions.append("Proximity_Score >= %s")
            params.append(proximity_score_min)
        if proximity_score_max is not None:
            conditions.append("Proximity_Score <= %s")
            params.append(proximity_score_max)

        total_items = count_items(cursor, table_name, conditions, params)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        results = fetch_data(cursor, table_name, conditions, params, items_per_page, offset)

        output = {
            "tableData": results,
            "totalPages": total_pages,
            "heatmapData": results  # Same data used for heatmap for simplicity; adjust if different data is needed
        }
        print(json.dumps(output))
        cursor.close()
    else:
        print(json.dumps({"error": "Failed to connect to the database."}))

    if conn:
        conn.close()

if __name__ == "__main__":
    main()

