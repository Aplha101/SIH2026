import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)
key = os.getenv("SUPABASE_KEY")
url = f"postgresql://postgres:{key}@db.kkjszxexisrfbctqllhn.supabase.co:5432/postgres"


def get_db_connection():
    return psycopg2.connect(url)

#SIGNUP / REGISTER

@app.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password') 
        full_name = data.get('full_name')
        role = data.get('role') 

        if not all([email, password, full_name, role]):
            return jsonify({"success": False, "error": "Missing fields"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    
        cursor.execute("SELECT id FROM profiles WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"success": False, "error": "Account with this email already exists"}), 409

        sql = """
            INSERT INTO profiles (role, full_name, email, password)
            VALUES (%s, %s, %s, %s) RETURNING id, role, full_name, email;
        """
        cursor.execute(sql, (role, full_name, email, password))
        new_user = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Account created", "user": new_user}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# LOGIN

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"success": False, "error": "Email and password required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("SELECT id, role, full_name, email, password FROM profiles WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()

        if user and user['password'] == password:
            del user['password'] 
            return jsonify({"success": True, "message": "Login successful", "user": user}), 200
        else:
            return jsonify({"success": False, "error": "Invalid email or password"}), 401

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



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

#SUBMIT A REQUEST BY STUDENT

@app.route("/requests", methods=["GET"])
def get_all_requests():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
        sql = """
            SELECT sr.*, p.full_name as student_name 
            FROM support_requests sr
            JOIN profiles p ON sr.student_id = p.id
            ORDER BY sr.created_at DESC
        """
        cursor.execute(sql)
        res = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return jsonify({"success": True, "data": res})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

#SUBMIT A NEW REQUEST

@app.route("/requests", methods=["POST"])
def create_request():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            INSERT INTO support_requests (student_id, symptoms_description, urgency_level)
            VALUES (%s, %s, %s) RETURNING id;
        """
        cursor.execute(sql, (data['student_id'], data['symptoms_description'], data['urgency_level']))
        new_id = cursor.fetchone()[0]
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Request created", "id": new_id}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

#COUNSELOR ACTION

@app.route("/requests/<request_id>/status", methods=["PATCH"])
def update_status(request_id):
    try:
        data = request.json
        new_status = data['status'] # e.g., 'in-progress' or 'resolved'
        
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = "UPDATE support_requests SET status = %s WHERE id = %s"
        cursor.execute(sql, (new_status, request_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Status updated successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask DB service on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
