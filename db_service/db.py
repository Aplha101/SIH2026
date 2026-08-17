import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
)

load_dotenv()

app = Flask(__name__)
CORS(app)
key = os.getenv("SUPABASE_KEY")
url = f"postgresql://postgres:{key}@db.kkjszxexisrfbctqllhn.supabase.co:5432/postgres"

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-prototype-key")
jwt = JWTManager(app)

def get_db_connection():
    return psycopg2.connect(url)

#SIGNUP / REGISTER

@app.route("/signup", methods=["POST"])
def signup():
    conn = None
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password') 
        full_name = data.get('full_name')
        role = data.get('role') 

        if not all([email, password, full_name, role]):
            return jsonify({"success": False, "error": "Missing fields"}), 400
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return jsonify({"success": False, "error": "Account with this email already exists"}), 409

            sql = """
                INSERT INTO users (role, full_name, email, password)
                VALUES (%s, %s, %s, %s) RETURNING id, role, full_name, email;
            """
            cursor.execute(sql, (role, full_name, email, hashed_password))
            new_user = cursor.fetchone()
            conn.commit()
           
        return jsonify({"success": True, "message": "Account created", "user": new_user}), 201
    except Exception as e:
        app.logger.error(f"Signup error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500
    finally:
        if conn: conn.close()

# LOGIN

@app.route("/login", methods=["POST"])
def login():
    conn = None

    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"success": False, "error": "Email and password required"}), 400

        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("SELECT id, role, full_name, email, password FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
        if user and check_password_hash(user['password'], password):
            access_token = create_access_token(
                identity=str(user['id']),
                additional_claims={"role": user['role']}
            )
            
            del user['password'] 
            return jsonify({
                "success": True, 
                "message": "Login successful", 
                "user": user,
                "token": access_token
            }), 200
        else:
            return jsonify({"success": False, "error": "Invalid email or password"}), 401
    except Exception as e:
        app.logger.error(f"Login error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500
    finally:
        if conn: conn.close()


# -------------------------------------------------------------
# DEFINE AND EXECUTE SQL QUERIES HERE IN PYTHON
# -------------------------------------------------------------


# Fetch All Users (SQL defined in Python)
@app.route("/get-all", methods=["GET"]) 
@jwt_required()
def get_all_users():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"success": False, "error": "Unauthorized Access"}), 403

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            sql = "SELECT id, role, full_name, email FROM users"
            cursor.execute(sql)
            res = cursor.fetchall()
            
        return jsonify({"success": True, "res": res})
    except Exception as e:
        app.logger.error(f"Get users error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500
    finally:
        if conn: conn.close()

#COUNSELOR ACTION

@app.route("/requests", methods=["GET"])
@jwt_required()
def get_all_requests():
    conn = None
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get("role")

        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            if user_role == "student":
                sql = """
                    SELECT sr.*, p.full_name as student_name 
                    FROM support_requests sr
                    JOIN users p ON sr.student_id = p.id
                    WHERE sr.student_id = %s
                    ORDER BY sr.created_at DESC
                """
                cursor.execute(sql, (current_user_id,))
            else:
                sql = """
                    SELECT sr.*, p.full_name as student_name 
                    FROM support_requests sr
                    JOIN users p ON sr.student_id = p.id
                    ORDER BY sr.created_at DESC
                """
                cursor.execute(sql)
            
            res = cursor.fetchall()
            
        return jsonify({"success": True, "data": res})
    except Exception as e:
        app.logger.error(f"Fetch requests error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500
    finally:
        if conn: conn.close()


@app.route("/requests", methods=["POST"])
@jwt_required()
def create_request():
    conn = None
    try:
        data = request.json
        student_id = get_jwt_identity() 
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO support_requests (student_id, symptoms_description, urgency_level)
                VALUES (%s, %s, %s) RETURNING id;
            """
            cursor.execute(sql, (student_id, data['symptoms_description'], data['urgency_level']))
            new_id = cursor.fetchone()[0]
            conn.commit()
            
        return jsonify({"success": True, "message": "Request created", "id": new_id}), 201
    except Exception as e:
        app.logger.error(f"Create request error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500
    finally:
        if conn: conn.close()


@app.route("/requests/<request_id>/status", methods=["PATCH"])
@jwt_required()
def update_status(request_id):
    conn = None
    try:
        claims = get_jwt()
        if claims.get("role") not in ["counselor", "admin"]:
            return jsonify({"success": False, "error": "Unauthorized to change status"}), 403

        data = request.json
        new_status = data['status']
        counselor_id = get_jwt_identity()
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql_update = "UPDATE support_requests SET status = %s WHERE id = %s"
            cursor.execute(sql_update, (new_status, request_id))
            
            sql_audit = """
                INSERT INTO audit_logs (action_type, target_request_id) 
                VALUES (%s, %s)
            """
            action_desc = f"Status updated to {new_status} by user {counselor_id}"
            cursor.execute(sql_audit, (action_desc, request_id))
            
            conn.commit()
            
        return jsonify({"success": True, "message": "Status updated and logged securely"})
    except Exception as e:
        if conn: conn.rollback() 
        app.logger.error(f"Status update error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500
    finally:
        if conn: conn.close()


if __name__ == '__main__':
    print("Starting Flask DB service on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)