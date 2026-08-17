import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from werkzeug.security import generate_password_hash, check_password_hash

from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)


load_dotenv()

app = Flask(__name__)

CORS(app, origins=[
    "http://localhost:3000",
    "https://sih-2026-fawn.vercel.app"
])

# JWT configuration
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

if not app.config["JWT_SECRET_KEY"]:
    raise RuntimeError("JWT_SECRET_KEY is not set in .env")

jwt = JWTManager(app)


# -------------------------------------------------------------
# DATABASE
# -------------------------------------------------------------

key = os.getenv("SUPABASE_KEY")

if not key:
    raise RuntimeError("SUPABASE_KEY is not set in .env")

key = os.getenv("SUPABASE_KEY")

url = (
    f"postgresql://postgres.kkjszxexisrfbctqllhn:{key}"
    f"@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
)


def get_db_connection():
    return psycopg2.connect(url)


# -------------------------------------------------------------
# SIGNUP / REGISTER
# -------------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "message": "API is running"
    })

@app.route("/signup", methods=["POST"])
def signup():

    conn = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid JSON"
            }), 400

        email = data.get("email")
        password = data.get("password")
        full_name = data.get("full_name")
        role = data.get("role")

        if not all([email, password, full_name, role]):
            return jsonify({
                "success": False,
                "error": "Missing fields"
            }), 400

        # Hash password before storing it
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        with conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        ) as cursor:

            # Check if account already exists
            cursor.execute(
                "SELECT id FROM users WHERE email = %s",
                (email,)
            )

            if cursor.fetchone():
                return jsonify({
                    "success": False,
                    "error": "Account with this email already exists"
                }), 409

            # Create user
            sql = """
                INSERT INTO users
                    (role, full_name, email, password)
                VALUES
                    (%s, %s, %s, %s)
                RETURNING id, role, full_name, email;
            """

            cursor.execute(
                sql,
                (
                    role,
                    full_name,
                    email,
                    hashed_password
                )
            )

            new_user = cursor.fetchone()

            conn.commit()

        return jsonify({
            "success": True,
            "message": "Account created",
            "user": new_user
        }), 201

    except Exception as e:

        if conn:
            conn.rollback()

        app.logger.error(f"Signup error: {e}")

        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

    finally:

        if conn:
            conn.close()



@app.route("/login", methods=["POST"])
def login():
    conn = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid JSON"
            }), 400
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({
                "success": False,
                "error": "Email and password required"
            }), 400

        conn = get_db_connection()

        with conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        ) as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    role,
                    full_name,
                    email,
                    password
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            user = cursor.fetchone()

        # Check password
        if not user or not check_password_hash(
            user["password"],
            password
        ):
            return jsonify({
                "success": False,
                "error": "Invalid email or password"
            }), 401

        # -----------------------------------------------------
        # CREATE JWT
        # -----------------------------------------------------

        access_token = create_access_token(
            identity=str(user["id"]),
            additional_claims={
                "role": user["role"]
            }
        )

        # Never send password back to frontend
        del user["password"]

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": user,
            "token": access_token
        }), 200

    except Exception as e:

        app.logger.error(f"Login error: {e}")

        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

    finally:

        if conn:
            conn.close()


# -------------------------------------------------------------
# FETCH ALL USERS
# ADMIN ONLY
# -------------------------------------------------------------

@app.route("/get-all", methods=["GET"])
@jwt_required()
def get_all_users():

    # Get information stored inside JWT
    claims = get_jwt()

    # Only admins can access all users
    if claims.get("role") != "admin":
        return jsonify({
            "success": False,
            "error": "Unauthorized Access"
        }), 403

    conn = None

    try:

        conn = get_db_connection()

        with conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        ) as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    role,
                    full_name,
                    email
                FROM users
                """
            )

            users = cursor.fetchall()

        return jsonify({
            "success": True,
            "users": users
        }), 200

    except Exception as e:

        app.logger.error(f"Get users error: {e}")

        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

    finally:

        if conn:
            conn.close()


# -------------------------------------------------------------
# GET SUPPORT REQUESTS
# -------------------------------------------------------------

@app.route("/requests", methods=["GET"])
@jwt_required()
def get_all_requests():

    conn = None

    try:

        # Get logged-in user's ID from JWT
        current_user_id = get_jwt_identity()

        # Get role from JWT
        claims = get_jwt()
        user_role = claims.get("role")

        conn = get_db_connection()

        with conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        ) as cursor:

            # Students only see their own requests
            if user_role == "student":

                sql = """
                    SELECT
                        sr.*,
                        p.full_name AS student_name
                    FROM support_requests sr
                    JOIN users p
                        ON sr.student_id = p.id
                    WHERE sr.student_id = %s
                    ORDER BY sr.created_at DESC
                """

                cursor.execute(
                    sql,
                    (current_user_id,)
                )

            # Counselors/admins see all requests
            elif user_role in ["counselor", "admin"]:

                sql = """
                    SELECT
                        sr.*,
                        p.full_name AS student_name
                    FROM support_requests sr
                    JOIN users p
                        ON sr.student_id = p.id
                    ORDER BY sr.created_at DESC
                """

                cursor.execute(sql)

            else:

                return jsonify({
                    "success": False,
                    "error": "Unauthorized"
                }), 403

            requests = cursor.fetchall()

        return jsonify({
            "success": True,
            "data": requests
        }), 200

    except Exception as e:

        app.logger.error(f"Fetch requests error: {e}")

        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

    finally:

        if conn:
            conn.close()


# -------------------------------------------------------------
# CREATE SUPPORT REQUEST
# STUDENT
# -------------------------------------------------------------

@app.route("/requests", methods=["POST"])
@jwt_required()
def create_request():

    conn = None

    try:

        # Get student ID directly from JWT
        student_id = get_jwt_identity()

        # Get request body
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid JSON"
            }), 400

        symptoms_description = data.get(
            "symptoms_description"
        )

        urgency_level = data.get(
            "urgency_level"
        )

        if not symptoms_description or not urgency_level:
            return jsonify({
                "success": False,
                "error": "Missing fields"
            }), 400

        conn = get_db_connection()

        with conn.cursor() as cursor:

            sql = """
                INSERT INTO support_requests
                    (
                        student_id,
                        symptoms_description,
                        urgency_level
                    )
                VALUES
                    (%s, %s, %s)
                RETURNING id;
            """

            cursor.execute(
                sql,
                (
                    student_id,
                    symptoms_description,
                    urgency_level
                )
            )

            new_id = cursor.fetchone()[0]

            conn.commit()

        return jsonify({
            "success": True,
            "message": "Request created",
            "id": new_id
        }), 201

    except Exception as e:

        if conn:
            conn.rollback()

        app.logger.error(
            f"Create request error: {e}"
        )

        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

    finally:

        if conn:
            conn.close()


# -------------------------------------------------------------
# UPDATE REQUEST STATUS
# COUNSELOR / ADMIN ONLY
# -------------------------------------------------------------

@app.route("/requests/<request_id>/status", methods=["PATCH"])
@jwt_required()
def update_status(request_id):

    conn = None

    try:

        claims = get_jwt()

        # Only counselor/admin can change status
        if claims.get("role") not in [
            "counselor",
            "admin"
        ]:

            return jsonify({
                "success": False,
                "error": "Unauthorized to change status"
            }), 403

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid JSON"
            }), 400

        new_status = data.get("status")

        if not new_status:
            return jsonify({
                "success": False,
                "error": "Status is required"
            }), 400

        # Get counselor/admin ID from JWT
        counselor_id = get_jwt_identity()

        conn = get_db_connection()

        with conn.cursor() as cursor:

            # Update request status
            sql_update = """
                UPDATE support_requests
                SET status = %s
                WHERE id = %s
            """

            cursor.execute(
                sql_update,
                (
                    new_status,
                    request_id
                )
            )

            # Audit log
            sql_audit = """
                INSERT INTO audit_logs
                    (
                        action_type,
                        target_request_id
                    )
                VALUES
                    (%s, %s)
            """

            action_desc = (
                f"Status updated to "
                f"{new_status} by user "
                f"{counselor_id}"
            )

            cursor.execute(
                sql_audit,
                (
                    action_desc,
                    request_id
                )
            )

            conn.commit()

        return jsonify({
            "success": True,
            "message": "Status updated and logged securely"
        }), 200

    except Exception as e:

        if conn:
            conn.rollback()

        app.logger.error(
            f"Status update error: {e}"
        )

        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

    finally:

        if conn:
            conn.close()

if __name__ == "__main__":

    print(
        "Starting Flask DB service on port 5000..."
    )

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )


@app.route("/me", methods=["GET"])
@jwt_required()
def me():

    user_id = get_jwt_identity()

    conn = get_db_connection()

    try:
        with conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        ) as cursor:

            cursor.execute("""
                SELECT id, role, full_name, email
                FROM users
                WHERE id = %s
            """, (user_id,))

            user = cursor.fetchone()

        if not user:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404

        return jsonify({
            "success": True,
            "user": user
        })

    finally:
        conn.close()