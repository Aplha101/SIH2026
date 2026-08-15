import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from flask import Flask, jsonify, request

load_dotenv()

app = Flask(__name__)
key = os.getenv("SUPABASE_KEY")
url = f"postgresql://postgres:{key}@db.kkjszxexisrfbctqllhn.supabase.co:5432/postgres"


def get_db_connection():
    return psycopg2.connect(url)


# -------------------------------------------------------------
# DEFINE AND EXECUTE SQL QUERIES HERE IN PYTHON
# -------------------------------------------------------------


# Fetch All Users (SQL defined in Python)
@app.route("/get-all", methods=["GET"])  # Changed to GET
def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    sql = "SELECT * FROM users"
    cursor.execute(sql)

    res = cursor.fetchall()
    cursor.close()
    conn.close()
    
    

    return jsonify({"success": True, "res": res})

if __name__ == '__main__':
    print("Starting Flask DB service on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)