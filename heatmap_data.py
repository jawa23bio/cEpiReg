#!/usr/bin/env python3
import cgi
import json
import pymysql

def db_connect():
    try:
        return pymysql.connect(host="bioed.bu.edu", user="bkapalli", passwd="bkapalli", db="Team_10", port=4253)
    except pymysql.MySQLError as e:
        print("Content-Type: text/html\n")
        return None

def fetch_heatmap_data(cell_type, page):
    conn = db_connect()
    if conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        table_name = f"linked_{cell_type}_all_chromosomes"
        items_per_page = 10
        offset = (page - 1) * items_per_page

        query = f"""
        SELECT Gene_ID, CRE_ID, Proximity_Score
        FROM {table_name}
        LIMIT %s OFFSET %s
        """
        cursor.execute(query, [items_per_page, offset])
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return data
    else:
        return []

def main():
    print("Content-Type: application/json\n")
    form = cgi.FieldStorage()
    cell_type = form.getvalue('cell_type')
    page = int(form.getvalue('page', 1))
    data = fetch_heatmap_data(cell_type, page)
    # Transform data into JSON suitable for heatmap visualization
    print(json.dumps(data))

if __name__ == "__main__":
    main()

