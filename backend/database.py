import sqlite3
import os


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")

os.makedirs(DATABASE_DIR, exist_ok=True)

DATABASE_PATH = os.path.join(
    DATABASE_DIR,
    "grievance.db"
)


def get_db_connection():

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    return connection


def create_tables():

    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student'
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS grievances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grievance_id TEXT UNIQUE NOT NULL,
            student_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT,
            priority TEXT,
            department TEXT,
            status TEXT DEFAULT 'Pending',
            admin_response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id)
        )
    """)

    connection.commit()

    connection.close()


def create_admin():

    connection = get_db_connection()

    admin = connection.execute(
        "SELECT id FROM users WHERE email = ?",
        ("admin@college.com",)
    ).fetchone()

    if not admin:

        connection.execute(
            """
            INSERT INTO users (name, email, password, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                "College Admin",
                "admin@college.com",
                "admin123",
                "admin"
            )
        )

        connection.commit()

    connection.close()