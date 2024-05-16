#!/usr/bin/env python3
import pymysql
import cgi
import json
import cgitb

# Enable error traceback
cgitb.enable()

# Establish a connection to the database
def connect_to_database():
    try:
        connection = pymysql.connect(
            host='bioed.bu.edu',
            user='jawa',
            password='jawa',
            database='Team_10',
            port=4253)
        return connection
    except pymysql.Error as e:
        print(e)
        return None

# Query the database for pie chart and table data
def query_data(selector, gene_name=None, chromosome=None, start=None, end=None):
    conditions = []
    params = []
    
    if gene_name:
        conditions.append("`Entrez_ID` REGEXP %s")
        params.append(gene_name)
    if chromosome:
        conditions.append("`Chr` = %s")
        params.append(chromosome)
    if start:
        conditions.append("`Start` >= %s")
        params.append(start)
    if end:
        conditions.append("`End` <= %s")
        params.append(end)

    if selector == "Pie":
        sql = """
            SELECT `Detailed_Annotation` as Type, COUNT(*) as Counts
            FROM Brain_annotation
            WHERE {}
            GROUP BY `Detailed_Annotation`
        """.format(" AND ".join(conditions))
    elif selector == "Table":
        sql = """
            SELECT Chr, Start, End, `Peak_Score`, `Annotation`, `Detailed_Annotation`, `Distance_to_TSS`, `Nearest_PromoterID`, `Entrez_ID`, `Gene_Name`, `Gene_Type`
            FROM Brain_annotation
            WHERE {}
        """.format(" AND ".join(conditions))
    else:
        return None

    try:
        connection = connect_to_database()
        if connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                results = cursor.fetchall()
                if not results:
                    return [("No data found",)]  # Return None if no data is present
                return results
    except pymysql.Error as e:
        print(e)
        return None
    finally:
        if connection:
            connection.close()

# Function to convert table data to text format
def convert_to_txt(headers, data):
    if not data:
        return ""

    # Convert data to text format
    txt_content = "\t".join(headers) + "\n"  # Include headers
    for row in data:
        txt_content += "\t".join(map(str, row)) + "\n"
    return txt_content

# Check for form data and process the request
def process_request():
    form = cgi.FieldStorage()
    print("Content-type: application/json\n")
    
    if not form:
        print(json.dumps({"error": "No form data received"}))
        return
        
    selector = form.getvalue("selector")
    gene_name = form.getvalue("gene_name")
    chromosome = form.getvalue("chromosome")
    start = form.getvalue("start")
    end = form.getvalue("end")
    
    if selector == "Download":
        # Handle download request
        data = None
        if gene_name and chromosome:
            data = query_data("Table", gene_name, chromosome=chromosome, start=start, end=end)
        elif gene_name:
            data = query_data("Table", gene_name, start=start, end=end)
        elif chromosome:
            data = query_data("Table", chromosome=chromosome, start=start, end=end)
            
        
        if data is not None:
            headers = ["Chr", "Start", "End", "Peak_Score", "Annotation", "Detailed_Annotation", "Distance_to_TSS", "Nearest_PromoterID", "Entrez_ID", "Gene_Name", "Gene_Type"]
            txt_content = convert_to_txt(headers, data)
            print(json.dumps(txt_content))
        else:
            print(json.dumps({"message": "No data present"}))
    else:
        # Handle other requests
        data = None
        if gene_name and chromosome:
            data = query_data(selector, gene_name, chromosome=chromosome, start=start, end=end)
        elif gene_name:
            data = query_data(selector, gene_name, start=start, end=end)
        elif chromosome:
            data = query_data(selector, chromosome=chromosome, start=start, end=end)
        
        if data is not None:
            print(json.dumps(data))
        else:
            print(json.dumps({"message": "No data present"}))

# Process the request
process_request()
