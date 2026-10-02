from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "army-safety-development-key"
)

DATABASE = "army_safety.db"


# =========================
# DATABASE CONNECTION
# =========================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# =========================
# CREATE DATABASE
# =========================

def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            soldier_id TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            duty_location TEXT DEFAULT 'Not Assigned',
            leave_count INTEGER DEFAULT 0,
            duty_status TEXT DEFAULT 'ON DUTY',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add columns to old databases

    try:

        conn.execute("""
            ALTER TABLE users
            ADD COLUMN duty_location TEXT DEFAULT 'Not Assigned'
        """)

    except sqlite3.OperationalError:

        pass


    try:

        conn.execute("""
            ALTER TABLE users
            ADD COLUMN leave_count INTEGER DEFAULT 0
        """)

    except sqlite3.OperationalError:

        pass


    try:

        conn.execute("""
            ALTER TABLE users
            ADD COLUMN duty_status TEXT DEFAULT 'ON DUTY'
        """)

    except sqlite3.OperationalError:

        pass


    # Alerts

    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            soldier_id TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            status TEXT DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # Check-ins

    conn.execute("""
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            soldier_id TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    conn.commit()

    conn.close()


# =========================
# HOME
# =========================

@app.route("/")
def home():

    return render_template("index.html")


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        soldier_id = request.form.get(
            "soldier_id",
            ""
        ).strip()

        duty_location = request.form.get(
            "duty_location",
            "Not Assigned"
        ).strip()

        leave_count = request.form.get(
            "leave_count",
            "0"
        ).strip()

        duty_status = request.form.get(
            "duty_status",
            "ON DUTY"
        ).strip()


        if not name:

            return render_template(
                "register.html",
                error="Please enter Soldier Name."
            )


        if len(name) < 2:

            return render_template(
                "register.html",
                error="Soldier Name must contain at least 2 characters."
            )


        if not soldier_id:

            return render_template(
                "register.html",
                error="Please enter Soldier ID."
            )


        if len(soldier_id) < 3:

            return render_template(
                "register.html",
                error="Soldier ID must contain at least 3 characters."
            )


        try:

            leave_count = int(leave_count)

        except ValueError:

            return render_template(
                "register.html",
                error="Leave count must be a number."
            )


        if leave_count < 0:

            return render_template(
                "register.html",
                error="Leave count cannot be negative."
            )


        if duty_status not in [
            "ON DUTY",
            "OFF DUTY",
            "ON LEAVE"
        ]:

            duty_status = "ON DUTY"


        conn = get_db()


        existing_user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE soldier_id = ?
            """,
            (soldier_id,)
        ).fetchone()


        if existing_user:

            conn.close()

            return render_template(
                "register.html",
                error="Soldier ID already exists."
            )


        default_password = "1234"

        password_hash = generate_password_hash(
            default_password
        )


        conn.execute(
            """
            INSERT INTO users
            (
                name,
                soldier_id,
                password,
                duty_location,
                leave_count,
                duty_status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                soldier_id,
                password_hash,
                duty_location,
                leave_count,
                duty_status
            )
        )


        conn.commit()

        conn.close()


        return render_template(
            "register.html",
            success="Registration successful! Default password is 1234."
        )


    return render_template("register.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        soldier_id = request.form.get(
            "soldier_id",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()


        if not soldier_id:

            return render_template(
                "login.html",
                error="Please enter your Soldier ID."
            )


        if not password:

            return render_template(
                "login.html",
                error="Please enter your password."
            )


        conn = get_db()


        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE soldier_id = ?
            """,
            (soldier_id,)
        ).fetchone()


        conn.close()


        if not user:

            return render_template(
                "login.html",
                error="Invalid Soldier ID or password."
            )


        if not check_password_hash(
            user["password"],
            password
        ):

            return render_template(
                "login.html",
                error="Invalid Soldier ID or password."
            )


        session["user_id"] = user["id"]

        session["soldier_name"] = user["name"]

        session["soldier_id"] = user["soldier_id"]


        return redirect(
            url_for("dashboard")
        )


    return render_template("login.html")


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    soldier_id = session.get(
        "soldier_id"
    )


    conn = get_db()


    soldier = conn.execute(
        """
        SELECT *
        FROM users
        WHERE soldier_id = ?
        """,
        (soldier_id,)
    ).fetchone()


    last_checkin = conn.execute(
        """
        SELECT *
        FROM checkins
        WHERE soldier_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (soldier_id,)
    ).fetchone()


    conn.close()


    if last_checkin:

        last_checkin_time = last_checkin[
            "created_at"
        ]

        try:

            checkin_datetime = datetime.strptime(
                last_checkin_time,
                "%Y-%m-%d %H:%M:%S"
            )

            current_time = datetime.utcnow()


            if current_time - checkin_datetime <= timedelta(hours=1):

                safety_status = "SAFE"

            else:

                safety_status = "CHECK-IN REQUIRED"


        except ValueError:

            safety_status = "CHECK-IN REQUIRED"

    else:

        safety_status = "CHECK-IN REQUIRED"

        last_checkin_time = "No check-in recorded"


    return render_template(
        "dashboard.html",

        soldier_name=session.get(
            "soldier_name"
        ),

        soldier_id=soldier_id,

        safety_status=safety_status,

        last_checkin=last_checkin_time,

        duty_location=soldier["duty_location"],

        leave_count=soldier["leave_count"],

        duty_status=soldier["duty_status"]
    )


# =========================
# UPDATE DUTY STATUS
# =========================

@app.route(
    "/update_duty_status",
    methods=["POST"]
)
def update_duty_status():

    if "user_id" not in session:

        return {
            "success": False,
            "message": "Please login first."
        }, 401


    soldier_id = session.get(
        "soldier_id"
    )


    duty_status = request.form.get(
        "duty_status",
        ""
    ).strip()


    allowed_statuses = [
        "ON DUTY",
        "OFF DUTY",
        "ON LEAVE"
    ]


    if duty_status not in allowed_statuses:

        return redirect(
            url_for("dashboard")
        )


    conn = get_db()


    conn.execute(
        """
        UPDATE users
        SET duty_status = ?
        WHERE soldier_id = ?
        """,
        (
            duty_status,
            soldier_id
        )
    )


    conn.commit()

    conn.close()


    return redirect(
        url_for("dashboard")
    )


# =========================
# SEND EMERGENCY ALERT
# =========================

@app.route(
    "/send_alert",
    methods=["POST"]
)
def send_alert():

    if "user_id" not in session:

        return {
            "success": False,
            "message": "Please login first."
        }, 401


    soldier_id = session.get(
        "soldier_id"
    )


    conn = get_db()


    conn.execute(
        """
        INSERT INTO alerts
        (soldier_id, alert_type, status)
        VALUES (?, ?, ?)
        """,
        (
            soldier_id,
            "EMERGENCY SOS",
            "ACTIVE"
        )
    )


    conn.commit()

    conn.close()


    return {
        "success": True,
        "message": "Emergency alert recorded successfully."
    }


# =========================
# ALERT HISTORY
# =========================

@app.route("/alert_history")
def alert_history():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    soldier_id = session.get(
        "soldier_id"
    )


    conn = get_db()


    alerts = conn.execute(
        """
        SELECT *
        FROM alerts
        WHERE soldier_id = ?
        ORDER BY created_at DESC
        """,
        (soldier_id,)
    ).fetchall()


    conn.close()


    return render_template(
        "alert_history.html",

        alerts=alerts,

        soldier_id=soldier_id
    )


# =========================
# SAFETY CHECK-IN
# =========================

@app.route(
    "/checkin",
    methods=["POST"]
)
def checkin():

    if "user_id" not in session:

        return {
            "success": False,
            "message": "Please login first."
        }, 401


    soldier_id = session.get(
        "soldier_id"
    )


    conn = get_db()


    conn.execute(
        """
        INSERT INTO checkins
        (soldier_id, status)
        VALUES (?, ?)
        """,
        (
            soldier_id,
            "SAFE"
        )
    )


    conn.commit()

    conn.close()


    return {
        "success": True,
        "message": "Safety check-in recorded successfully."
    }


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================
# START SERVER
# =========================

init_db()


if __name__ == "__main__":

    app.run(debug=True)