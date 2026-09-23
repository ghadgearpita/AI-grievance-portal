from flask import Flask, request, jsonify, send_from_directory
from database import create_tables, create_admin, get_db_connection
from ai_classifier import classify_grievance
from ai_priority import detect_priority
import os

app = Flask(__name__)


# =========================================================
# FOLDER PATHS
# =========================================================

BASE_FOLDER = os.path.dirname(
    os.path.dirname(__file__)
)

FRONTEND_FOLDER = os.path.join(
    BASE_FOLDER,
    "frontend"
)

ADMIN_FOLDER = os.path.join(
    BASE_FOLDER,
    "admin"
)


# =========================================================
# DATABASE SETUP
# =========================================================

create_tables()
create_admin()


# =========================================================
# STUDENT HOME PAGE
# =========================================================

@app.route("/")
def home():

    return send_from_directory(
        FRONTEND_FOLDER,
        "register.html"
    )


# =========================================================
# ADMIN HOME PAGE
# =========================================================

@app.route("/admin")
def admin_portal():

    return send_from_directory(
        ADMIN_FOLDER,
        "admin-login.html"
    )


@app.route("/admin/")
def admin_portal_slash():

    return send_from_directory(
        ADMIN_FOLDER,
        "admin-login.html"
    )


# =========================================================
# STUDENT REGISTRATION
# =========================================================

@app.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:

        return jsonify({
            "message": "All fields are required"
        }), 400

    connection = get_db_connection()

    try:

        connection.execute(
            """
            INSERT INTO users
            (name, email, password)
            VALUES (?, ?, ?)
            """,
            (
                name,
                email,
                password
            )
        )

        connection.commit()

        return jsonify({
            "message": "Registration successful!"
        }), 201

    except Exception:

        return jsonify({
            "message": "Email already registered"
        }), 400

    finally:

        connection.close()


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:

        return jsonify({
            "message": "Email and password are required"
        }), 400

    connection = get_db_connection()

    user = connection.execute(
        """
        SELECT
            id,
            name,
            email,
            role
        FROM users
        WHERE email = ?
        AND password = ?
        """,
        (
            email,
            password
        )
    ).fetchone()

    connection.close()

    if user:

        return jsonify({

            "message": "Login successful!",

            "user": {

                "id": user["id"],

                "name": user["name"],

                "email": user["email"],

                "role": user["role"]

            }

        }), 200

    return jsonify({
        "message": "Invalid email or password"
    }), 401


# =========================================================
# STUDENT - SUBMIT GRIEVANCE
# =========================================================

@app.route("/submit-grievance", methods=["POST"])
def submit_grievance():

    data = request.get_json()

    student_id = data.get("student_id")
    title = data.get("title")
    description = data.get("description")
    category = data.get("category")

    ai_category = classify_grievance(title, description)
    ai_priority = detect_priority(title, description)

    if (
        not student_id
        or not title
        or not description
        or not category
    ):

        return jsonify({
            "message": "All fields are required"
        }), 400

    connection = get_db_connection()

    try:

        count = connection.execute(
            "SELECT COUNT(*) FROM grievances"
        ).fetchone()[0]

        grievance_id = f"GRV-{count + 1:04d}"

        connection.execute(
            """
            INSERT INTO grievances
            (
                grievance_id,
                student_id,
                title,
                description,
                category,
                priority
            )
            VALUES (?, ?, ?, ?, ?,?)
            """,
            (
                grievance_id,
                student_id,
                title,
                description,
                ai_category,
                ai_priority
            )
        )

        connection.commit()

        return jsonify({

            "message":
                "Grievance submitted successfully!",

            "grievance_id":
                grievance_id

        }), 201

    except Exception as error:

        return jsonify({

            "message":
                "Failed to submit grievance",

            "error":
                str(error)

        }), 500

    finally:

        connection.close()


# =========================================================
# STUDENT - MY GRIEVANCES
# =========================================================

@app.route(
    "/my-grievances/<int:student_id>",
    methods=["GET"]
)
def my_grievances(student_id):

    connection = get_db_connection()

    grievances = connection.execute(
        """
        SELECT

            grievance_id,

            title,

            description,

            category,

            status

        FROM grievances

        WHERE student_id = ?

        ORDER BY id DESC
        """,
        (student_id,)
    ).fetchall()

    connection.close()

    return jsonify([
        dict(grievance)
        for grievance in grievances
    ])


# =========================================================
# STUDENT - TRACK STATUS
# =========================================================

@app.route(
    "/track-status/<grievance_id>/<int:student_id>",
    methods=["GET"]
)
def track_status(
    grievance_id,
    student_id
):

    connection = get_db_connection()

    grievance = connection.execute(
        """
        SELECT

            grievance_id,

            title,

            category,

            status

        FROM grievances

        WHERE grievance_id = ?

        AND student_id = ?
        """,
        (
            grievance_id,
            student_id
        )
    ).fetchone()

    connection.close()

    if grievance:

        return jsonify({

            "grievance_id":
                grievance["grievance_id"],

            "title":
                grievance["title"],

            "category":
                grievance["category"],

            "status":
                grievance["status"]

        }), 200

    return jsonify({
        "message": "Grievance not found"
    }), 404


# =========================================================
# ADMIN - VIEW ALL GRIEVANCES
# =========================================================

@app.route(
    "/admin/grievances",
    methods=["GET"]
)
def admin_grievances():

    connection = get_db_connection()

    grievances = connection.execute(
        """
        SELECT

            grievances.grievance_id,

            users.name AS student_name,

            grievances.title,

            grievances.description,

            grievances.category,

            grievances.priority,

            grievances.department,

            grievances.status

        FROM grievances

        JOIN users

        ON grievances.student_id = users.id

        ORDER BY grievances.id DESC
        """
    ).fetchall()

    connection.close()

    return jsonify([
        dict(grievance)
        for grievance in grievances
    ])


# =========================================================
# ADMIN - UPDATE DEPARTMENT
# =========================================================

@app.route(
    "/admin/update-department",
    methods=["PUT"]
)
def update_department():

    data = request.get_json()

    grievance_id = data.get(
        "grievance_id"
    )

    department = data.get(
        "department"
    )

    if not grievance_id or not department:

        return jsonify({

            "message":
                "Grievance ID and department are required"

        }), 400

    allowed_departments = [

        "Academic Department",

        "Hostel Department",

        "Library Department",

        "Examination Department",

        "Scholarship Department",

        "Infrastructure Department",

        "General Administration"

    ]

    if department not in allowed_departments:

        return jsonify({

            "message":
                "Invalid department"

        }), 400

    connection = get_db_connection()

    grievance = connection.execute(
        """
        SELECT id

        FROM grievances

        WHERE grievance_id = ?
        """,
        (grievance_id,)
    ).fetchone()

    if not grievance:

        connection.close()

        return jsonify({

            "message":
                "Grievance not found"

        }), 404

    connection.execute(
        """
        UPDATE grievances

        SET department = ?

        WHERE grievance_id = ?
        """,
        (
            department,
            grievance_id
        )
    )

    connection.commit()

    connection.close()

    return jsonify({

        "message":
            "Department updated successfully!"

    }), 200


# =========================================================
# ADMIN - UPDATE STATUS
# =========================================================

@app.route(
    "/admin/update-status",
    methods=["PUT"]
)
def update_status():

    data = request.get_json()

    grievance_id = data.get(
        "grievance_id"
    )

    status = data.get(
        "status"
    )

    if not grievance_id or not status:

        return jsonify({

            "message":
                "Grievance ID and status are required"

        }), 400

    allowed_statuses = [

        "Pending",

        "In Progress",

        "Resolved"

    ]

    if status not in allowed_statuses:

        return jsonify({
            "message": "Invalid status"
        }), 400

    connection = get_db_connection()

    grievance = connection.execute(
        """
        SELECT id

        FROM grievances

        WHERE grievance_id = ?
        """,
        (grievance_id,)
    ).fetchone()

    if not grievance:

        connection.close()

        return jsonify({

            "message":
                "Grievance not found"

        }), 404

    connection.execute(
        """
        UPDATE grievances

        SET status = ?

        WHERE grievance_id = ?
        """,
        (
            status,
            grievance_id
        )
    )

    connection.commit()

    connection.close()

    return jsonify({

        "message":
            "Status updated successfully!"

    }), 200


# =========================================================
# ADMIN - STATISTICS
# =========================================================

@app.route(
    "/admin/statistics",
    methods=["GET"]
)
def admin_statistics():

    connection = get_db_connection()

    total = connection.execute(
        """
        SELECT COUNT(*)
        FROM grievances
        """
    ).fetchone()[0]

    pending = connection.execute(
        """
        SELECT COUNT(*)

        FROM grievances

        WHERE status = ?
        """,
        ("Pending",)
    ).fetchone()[0]

    in_progress = connection.execute(
        """
        SELECT COUNT(*)

        FROM grievances

        WHERE status = ?
        """,
        ("In Progress",)
    ).fetchone()[0]

    resolved = connection.execute(
        """
        SELECT COUNT(*)

        FROM grievances

        WHERE status = ?
        """,
        ("Resolved",)
    ).fetchone()[0]

    connection.close()

    return jsonify({

        "total":
            total,

        "pending":
            pending,

        "in_progress":
            in_progress,

        "resolved":
            resolved

    }), 200


# =========================================================
# ADMIN STATIC FILES
# =========================================================

@app.route(
    "/admin/<path:filename>"
)
def admin_files(filename):

    return send_from_directory(
        ADMIN_FOLDER,
        filename
    )


# =========================================================
# STUDENT STATIC FILES
# =========================================================

@app.route(
    "/<path:filename>"
)
def frontend_files(filename):

    return send_from_directory(
        FRONTEND_FOLDER,
        filename
    )


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )