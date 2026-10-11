from flask import Flask, render_template, request, redirect, url_for, session
from datetime import timedelta, date
import os
import re
import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


load_dotenv()

app = Flask(__name__)

# Secret key for Flask sessions
app.secret_key = os.getenv(
    "SECRET_KEY",
    "job_analyzer_development_secret_key"
)

# Remember Me session duration
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

# Profile picture upload settings
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

ALLOWED_PROFILE_PICTURE_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp"
}


# -----------------------------
# MySQL Database Connection
# -----------------------------
def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

    return connection


# -----------------------------
# Home Page
# -----------------------------
@app.route("/")
def home():

    # ---------------------------------
    # Logged-out user
    # ---------------------------------

    if "user_id" not in session:

        return render_template(
            "home.html",
            logged_in=False
        )


    # ---------------------------------
    # Logged-in user
    # Get real application statistics
    # ---------------------------------

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        stats_query = """
            SELECT

                COUNT(*) AS total_applications,

                SUM(
                    CASE
                        WHEN status = 'Interview' THEN 1
                        ELSE 0
                    END
                ) AS interviews,

                SUM(
                    CASE
                        WHEN status = 'Selected' THEN 1
                        ELSE 0
                    END
                ) AS selected,

                SUM(
                    CASE
                        WHEN status = 'Rejected' THEN 1
                        ELSE 0
                    END
                ) AS rejected

            FROM applications

            WHERE user_id = %s
        """

        cursor.execute(
            stats_query,
            (session["user_id"],)
        )

        stats = cursor.fetchone()

        cursor.execute(
            "SELECT profile_picture FROM users WHERE id = %s",
            (session["user_id"],)
        )
        user_profile = cursor.fetchone()

    finally:

        cursor.close()
        connection.close()


    # ---------------------------------
    # Send statistics to Home page
    # ---------------------------------

    return render_template(

        "home.html",

        logged_in=True,

        total_applications=
            stats["total_applications"] or 0,

        interviews=
            stats["interviews"] or 0,

        selected=
            stats["selected"] or 0,

        rejected=
            stats["rejected"] or 0,

        profile_picture=(
            user_profile["profile_picture"]
            if user_profile else None
        )
    )


# -----------------------------
# Register
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Check whether passwords match
        if password != confirm_password:
            return "Passwords do not match."

        # Hash the password
        hashed_password = generate_password_hash(password)

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            query = """
                INSERT INTO users (name, email, password)
                VALUES (%s, %s, %s)
            """

            values = (
                name,
                email,
                hashed_password
            )

            cursor.execute(query, values)
            connection.commit()

            return redirect(url_for("login"))

        except mysql.connector.IntegrityError:

            return "An account with this email already exists."

        finally:

            cursor.close()
            connection.close()

    return render_template("register.html")


# -----------------------------
# Login
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        # Get Remember Me value
        remember = request.form.get("remember")

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            # Find user by email
            query = """
                SELECT id, name, email, password
                FROM users
                WHERE email = %s
            """

            cursor.execute(query, (email,))

            user = cursor.fetchone()

            # -------------------------
            # User does not exist
            # -------------------------

            if user is None:

                return render_template(
                    "login.html",
                    error="No account found with this email. Please register first."
                )

            # -------------------------
            # Check password
            # -------------------------

            if not check_password_hash(
                user["password"],
                password
            ):

                return render_template(
                    "login.html",
                    error="Incorrect password. Please try again."
                )

            # -------------------------
            # Login successful
            # -------------------------

            # Set session duration
            session.permanent = remember == "on"

            # Store logged-in user information
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            return redirect(url_for("home"))

        finally:

            cursor.close()
            connection.close()

    return render_template("login.html")


# -----------------------------
# Add Application
# -----------------------------
@app.route("/add-application", methods=["GET", "POST"])
def add_application():

    # User must be logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        company = request.form["company"]
        job_title = request.form["job_title"]
        location = request.form["location"]
        job_type = request.form["job_type"]
        application_date = request.form["application_date"]
        status = request.form["status"]
        job_description = request.form["job_description"]
        notes = request.form["notes"]

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            query = """
                INSERT INTO applications
                (
                    user_id,
                    company,
                    job_title,
                    location,
                    job_type,
                    application_date,
                    status,
                    job_description,
                    notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                session["user_id"],
                company,
                job_title,
                location,
                job_type,
                application_date,
                status,
                job_description,
                notes
            )

            cursor.execute(query, values)
            connection.commit()

            return redirect(url_for("dashboard"))

        finally:

            cursor.close()
            connection.close()

    return render_template("add_application.html")


# -----------------------------
# My Applications
# -----------------------------
@app.route("/applications")
def applications():

    # User must be logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        query = """
            SELECT
                id,
                company,
                job_title,
                location,
                job_type,
                application_date,
                status,
                job_description,
                notes
            FROM applications
            WHERE user_id = %s
            ORDER BY application_date DESC, id DESC
        """

        cursor.execute(query, (session["user_id"],))

        applications = cursor.fetchall()

        return render_template(
            "applications.html",
            applications=applications
        )

    finally:

        cursor.close()
        connection.close()


# -----------------------------
# View Application
# -----------------------------
@app.route("/application/<int:application_id>")
def view_application(application_id):

    # User must be logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        query = """
            SELECT
                id,
                company,
                job_title,
                location,
                job_type,
                application_date,
                status,
                job_description,
                notes
            FROM applications
            WHERE id = %s
            AND user_id = %s
        """

        cursor.execute(
            query,
            (application_id, session["user_id"])
        )

        application = cursor.fetchone()

        if application is None:
            return "Application not found.", 404

        return render_template(
            "view_application.html",
            application=application
        )

    finally:

        cursor.close()
        connection.close()


# -----------------------------
# Edit Application
# -----------------------------
@app.route("/application/<int:application_id>/edit", methods=["GET", "POST"])
def edit_application(application_id):

    # User must be logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # Get the application belonging to the logged-in user
        query = """
            SELECT
                id,
                company,
                job_title,
                location,
                job_type,
                application_date,
                status,
                job_description,
                notes
            FROM applications
            WHERE id = %s
            AND user_id = %s
        """

        cursor.execute(
            query,
            (application_id, session["user_id"])
        )

        application = cursor.fetchone()

        # Application not found
        if application is None:
            return "Application not found.", 404

        # Update application
        if request.method == "POST":

            company = request.form["company"]
            job_title = request.form["job_title"]
            location = request.form["location"]
            job_type = request.form["job_type"]
            application_date = request.form["application_date"]
            status = request.form["status"]
            job_description = request.form["job_description"]
            notes = request.form["notes"]

            update_query = """
                UPDATE applications
                SET
                    company = %s,
                    job_title = %s,
                    location = %s,
                    job_type = %s,
                    application_date = %s,
                    status = %s,
                    job_description = %s,
                    notes = %s
                WHERE id = %s
                AND user_id = %s
            """

            values = (
                company,
                job_title,
                location,
                job_type,
                application_date,
                status,
                job_description,
                notes,
                application_id,
                session["user_id"]
            )

            cursor.execute(update_query, values)
            connection.commit()

            return redirect(url_for("applications"))

        # Show edit form
        return render_template(
            "edit_application.html",
            application=application
        )

    finally:

        cursor.close()
        connection.close()


# -----------------------------
# Delete Application
# -----------------------------
@app.route("/application/<int:application_id>/delete", methods=["POST"])
def delete_application(application_id):

    # User must be logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        query = """
            DELETE FROM applications
            WHERE id = %s
            AND user_id = %s
        """

        cursor.execute(
            query,
            (application_id, session["user_id"])
        )

        connection.commit()

        return redirect(url_for("applications"))

    finally:

        cursor.close()
        connection.close()


# -----------------------------
# Dashboard
# -----------------------------
@app.route("/dashboard")
def dashboard():

    # User must be logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # ---------------------------------
        # 1. Get application statistics
        # ---------------------------------

        stats_query = """
            SELECT
                COUNT(*) AS total_applications,

                SUM(
                    CASE
                        WHEN status = 'Applied' THEN 1
                        ELSE 0
                    END
                ) AS applied,

                SUM(
                    CASE
                        WHEN status = 'Interview' THEN 1
                        ELSE 0
                    END
                ) AS interviews,

                SUM(
                    CASE
                        WHEN status = 'Selected' THEN 1
                        ELSE 0
                    END
                ) AS selected,

                SUM(
                    CASE
                        WHEN status = 'Rejected' THEN 1
                        ELSE 0
                    END
                ) AS rejected

            FROM applications
            WHERE user_id = %s
        """

        cursor.execute(
            stats_query,
            (session["user_id"],)
        )

        stats = cursor.fetchone()

        cursor.execute(
            "SELECT profile_picture FROM users WHERE id = %s",
            (session["user_id"],)
        )
        user_profile = cursor.fetchone()

        # ---------------------------------
        # 2. Get monthly application counts
        # ---------------------------------

        monthly_query = """
            SELECT
                YEAR(application_date) AS year,
                MONTH(application_date) AS month,
                COUNT(*) AS total

            FROM applications

            WHERE user_id = %s

            GROUP BY
                YEAR(application_date),
                MONTH(application_date)

            ORDER BY
                year,
                month
        """

        cursor.execute(
            monthly_query,
            (session["user_id"],)
        )

        monthly_results = cursor.fetchall()

        # ---------------------------------
        # 3. Create dictionary of database data
        # ---------------------------------

        monthly_data = {}

        for row in monthly_results:

            key = (
                row["year"],
                row["month"]
            )

            monthly_data[key] = row["total"]

        # ---------------------------------
        # 4. Generate the last 6 months
        # ---------------------------------

        current_month = date.today().replace(day=1)

        months = []

        for i in range(5, -1, -1):

            month = current_month.month - i
            year = current_month.year

            while month <= 0:
                month += 12
                year -= 1

            month_key = (year, month)

            month_name = date(
                year,
                month,
                1
            ).strftime("%b")

            application_count = monthly_data.get(
                month_key,
                0
            )

            months.append({
                "name": month_name,
                "count": application_count
            })

        # ---------------------------------
        # 5. Calculate chart bar heights
        # ---------------------------------

        maximum = max(
            [month["count"] for month in months],
            default=0
        )

        for month in months:

            if maximum == 0:
                month["height"] = 10

            else:
                month["height"] = (
                    month["count"] / maximum
                ) * 100

        # ---------------------------------
        # 6. Send everything to dashboard
        # ---------------------------------

        return render_template(
            "dashboard.html",

            total_applications=
                stats["total_applications"],

            applied=
                stats["applied"] or 0,

            interviews=
                stats["interviews"] or 0,

            selected=
                stats["selected"] or 0,

            rejected=
                stats["rejected"] or 0,

            months=months,

            profile_picture=(
                user_profile["profile_picture"]
                if user_profile else None
            )
        )

    finally:

        cursor.close()
        connection.close()


# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================================================
# USER PROFILE
# =========================================================
@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # Get user information
        cursor.execute(
            """
            SELECT id, name, email, profile_picture
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        # Get saved skills
        cursor.execute(
            """
            SELECT skill
            FROM user_skills
            WHERE user_id = %s
            ORDER BY skill
            """,
            (session["user_id"],)
        )

        skill_rows = cursor.fetchall()

        saved_skills = [
            row["skill"]
            for row in skill_rows
        ]

    finally:

        cursor.close()
        connection.close()

    profile_success = session.pop("profile_success", None)

    return render_template(
        "profile.html",
        user=user,
        saved_skills=saved_skills,
        profile_success=profile_success
    )


# =========================================================
# UPLOAD / CHANGE PROFILE PICTURE
# =========================================================
@app.route("/profile/upload-picture", methods=["POST"])
def upload_profile_picture():

    # User must be logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    file = request.files.get("profile_picture")

    if file is None or file.filename == "":
        return "Please select a profile picture.", 400

    # Get the file extension
    original_filename = secure_filename(file.filename)
    extension = os.path.splitext(original_filename)[1].lower().lstrip(".")

    # Only allow supported image formats
    if extension not in ALLOWED_PROFILE_PICTURE_EXTENSIONS:
        return "Only JPG, JPEG, PNG, and WEBP images are allowed.", 400

    upload_folder = os.path.join(
        app.static_folder,
        "uploads",
        "profile_pictures"
    )

    os.makedirs(upload_folder, exist_ok=True)

    # Use one predictable filename per user.
    filename = f"user_{session['user_id']}.{extension}"
    file_path = os.path.join(upload_folder, filename)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # Get the old profile picture filename
        cursor.execute(
            """
            SELECT profile_picture
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        # Save the new image
        file.save(file_path)

        # Update database
        cursor.execute(
            """
            UPDATE users
            SET profile_picture = %s
            WHERE id = %s
            """,
            (filename, session["user_id"])
        )

        connection.commit()

        # Delete the old image after the new one is saved.
        old_filename = user["profile_picture"] if user else None

        if old_filename and old_filename != filename:
            old_path = os.path.join(upload_folder, old_filename)

            if os.path.exists(old_path):
                os.remove(old_path)

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("profile"))


# =========================================================
# EDIT PROFILE NAME
# =========================================================
def render_profile_with_error(error_message, error_modal):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, name, email, profile_picture
            FROM users
            WHERE id = %s
        """, (session["user_id"],))
        user = cursor.fetchone()
        cursor.execute("""
            SELECT skill FROM user_skills
            WHERE user_id = %s ORDER BY skill
        """, (session["user_id"],))
        saved_skills = [row["skill"] for row in cursor.fetchall()]
    finally:
        cursor.close()
        connection.close()
    return render_template("profile.html", user=user, saved_skills=saved_skills, profile_error=error_message, profile_error_modal=error_modal)


@app.route("/profile/edit-name", methods=["POST"])
def edit_profile_name():

    # User must be logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    name = request.form.get("name", "").strip()

    # Basic validation
    if not name:
        return "Name cannot be empty.", 400

    if len(name) > 100:
        return "Name must be 100 characters or less.", 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE users
            SET name = %s
            WHERE id = %s
            """,
            (name, session["user_id"])
        )

        connection.commit()

        # Keep the current login session in sync
        session["user_name"] = name

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("profile"))


# =========================================================
# EDIT PROFILE EMAIL
# =========================================================
@app.route("/profile/edit-email", methods=["POST"])
def edit_profile_email():

    # User must be logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    email = request.form.get("email", "").strip().lower()
    current_password = request.form.get("current_password", "")

    # Basic validation
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        return render_profile_with_error("Please enter a valid email address.", "email" )

    if len(email) > 150:
        return render_profile_with_error("Email must be 150 characters or less.", "email")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # Get current password
        cursor.execute(
            """
            SELECT password
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        if user is None:
            return render_profile_with_error("User not found.", "email")

        # Require the current password before changing email
        if not check_password_hash(
            user["password"],
            current_password
        ):
            return render_profile_with_error("Current password is incorrect.", "email")

        # Make sure another account is not already using this email
        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email = %s
            AND id != %s
            """,
            (email, session["user_id"])
        )

        existing_user = cursor.fetchone()

        if existing_user is not None:
            return render_profile_with_error("That email address is already being used by another account.", "email")

        cursor.execute(
            """
            UPDATE users
            SET email = %s
            WHERE id = %s
            """,
            (email, session["user_id"])
        )

        connection.commit()

        # Keep the current login session in sync
        session["user_email"] = email

        # Show a success message on the Profile page
        session["profile_success"] = "Email changed successfully!"

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("profile"))


# =========================================================
# CHANGE PASSWORD
# =========================================================
@app.route("/profile/change-password", methods=["POST"])
def change_password():

    # User must be logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    # Basic validation
    if not current_password:
        return render_profile_with_error("Please enter your current password.", "password")

    if not new_password:
        return render_profile_with_error("New password cannot be empty.", "password")

    if new_password != confirm_password:
        return render_profile_with_error("New passwords do not match.", "password")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT password
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        if user is None:
            return render_profile_with_error("User not found.", "password")

        # Verify the current password
        if not check_password_hash(
            user["password"],
            current_password
        ):
            return render_profile_with_error("Current password is incorrect.", "password")

        # Hash the new password before storing it
        hashed_password = generate_password_hash(new_password)

        cursor.execute(
            """
            UPDATE users
            SET password = %s
            WHERE id = %s
            """,
            (hashed_password, session["user_id"])
        )

        connection.commit()

        # Show a success message on the Profile page
        session["profile_success"] = "Password changed successfully!"

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("profile"))


# =========================================================
# UPDATE PROFILE SKILLS
# =========================================================
@app.route("/profile/update-skills", methods=["POST"])
def update_profile_skills():

    # User must be logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    skills_text = request.form.get("skills", "")

    # Read comma-separated skills, remove empty values,
    # and avoid duplicate skills (case-insensitive).
    skills = []
    seen = set()

    for skill in skills_text.split(","):
        skill = skill.strip()

        if not skill:
            continue

        skill_key = skill.lower()

        if skill_key not in seen:
            seen.add(skill_key)
            skills.append(skill)

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # Replace the user's existing saved skills.
        cursor.execute(
            """
            DELETE FROM user_skills
            WHERE user_id = %s
            """,
            (session["user_id"],)
        )

        for skill in skills:
            cursor.execute(
                """
                INSERT INTO user_skills (user_id, skill, source)
                VALUES (%s, %s, %s)
                """,
                (session["user_id"], skill, "manual")
            )

        connection.commit()

        session["profile_success"] = "Skills updated successfully!"

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("profile"))


# =========================================================
# SKILL ANALYZER
# =========================================================
@app.route("/skill-analyzer", methods=["GET", "POST"])
def skill_analyzer():

    # User must be logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    matched_skills = []
    missing_skills = []
    job_skills = []
    match_percentage = None

    # =====================================================
    # GET SAVED USER SKILLS
    # =====================================================

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT skill
            FROM user_skills
            WHERE user_id = %s
            ORDER BY skill
            """,
            (session["user_id"],)
        )

        saved_skill_rows = cursor.fetchall()

        saved_skills = [
            row["skill"]
            for row in saved_skill_rows
        ]

    finally:

        cursor.close()
        connection.close()

    # =====================================================
    # HANDLE FORM SUBMISSION
    # =====================================================

    if request.method == "POST":

        # -------------------------------------------------
        # SAVE USER SKILLS
        # -------------------------------------------------
        # The Skill Analyzer page also allows the user to
        # save a comma-separated skill profile.
        if "user_skills" in request.form:

            skills_text = request.form.get("user_skills", "")

            skills = []
            seen = set()

            for skill in skills_text.split(","):
                skill = skill.strip()

                if not skill:
                    continue

                skill_key = skill.lower()

                if skill_key not in seen:
                    seen.add(skill_key)
                    skills.append(skill)

            connection = get_db_connection()
            cursor = connection.cursor()

            try:

                cursor.execute(
                    """
                    DELETE FROM user_skills
                    WHERE user_id = %s
                    """,
                    (session["user_id"],)
                )

                for skill in skills:
                    cursor.execute(
                        """
                        INSERT INTO user_skills (user_id, skill, source)
                        VALUES (%s, %s, %s)
                        """,
                        (session["user_id"], skill, "manual")
                    )

                connection.commit()
                session["skill_success"] = "Skills saved successfully!"

            finally:
                cursor.close()
                connection.close()

            return redirect(url_for("skill_analyzer"))

        # -------------------------------------------------
        # ANALYZE JOB DESCRIPTION
        # -------------------------------------------------
        job_description = request.form.get(
            "job_description",
            ""
        ).strip()

        # =================================================
        # GET USER SKILLS
        # =================================================

        user_skills = {
            skill.strip().lower()
            for skill in saved_skills
            if skill.strip()
        }

        # =================================================
        # INDUSTRY-INDEPENDENT SKILL LIST
        # =================================================

        skill_list = [

            # Programming & IT
            "python", "java", "c", "c++", "c#", "sql", "mysql",
            "postgresql", "mongodb", "html", "css", "javascript",
            "typescript", "flask", "django", "react", "node.js",
            "pandas", "numpy", "matplotlib", "seaborn",
            "scikit-learn", "machine learning", "deep learning",
            "data analysis", "data science",
            "artificial intelligence", "git", "github",
            "docker", "kubernetes", "aws", "azure",
            "google cloud", "rest api", "api", "linux",
            "testing", "software testing", "selenium", "jira",

            # Microsoft / Office
            "microsoft excel", "excel", "microsoft word", "word",
            "powerpoint", "power bi", "tableau", "ms office",

            # Management / MBA
            "business analysis", "business development",
            "business strategy", "project management",
            "product management", "operations management",
            "operations", "supply chain management",
            "supply chain", "market research",
            "strategic planning", "financial analysis",
            "risk management",
            "customer relationship management", "crm",

            # Marketing
            "digital marketing", "marketing",
            "content marketing", "social media marketing",
            "social media", "search engine optimization",
            "seo", "search engine marketing", "sem",
            "google ads", "advertising",
            "brand management", "email marketing",

            # Sales
            "sales", "lead generation", "client management",
            "customer relationship", "negotiation",
            "cold calling", "telecalling", "salesforce",

            # Human Resources
            "human resources", "hr", "recruitment",
            "talent acquisition", "employee relations",
            "employee engagement", "onboarding", "payroll",
            "performance management", "hr operations",
            "hrms", "workday", "interviewing",

            # Finance / Accounting
            "accounting", "finance", "financial reporting",
            "financial planning", "budgeting", "auditing",
            "taxation", "gst", "tally", "tally erp",
            "bookkeeping", "accounts payable",
            "accounts receivable", "bank reconciliation",

            # Banking
            "banking", "retail banking", "investment banking",
            "commercial banking", "loan processing",
            "credit analysis", "credit assessment",
            "kyc", "know your customer",
            "customer service", "financial services",
            "banking operations",

            # Communication / General
            "communication", "verbal communication",
            "written communication", "presentation",
            "public speaking", "teamwork", "leadership",
            "problem solving", "time management",
            "decision making", "analytical skills",
            "interpersonal skills",

            # Administration
            "documentation", "data entry", "administration",
            "administrative support",
            "office administration", "record keeping",
            "email management", "calendar management",

            # Education / Training
            "teaching", "training", "lesson planning",
            "curriculum development",
            "classroom management", "research",

            # Design / Creative
            "graphic design", "ui design", "ux design",
            "figma", "adobe photoshop",
            "adobe illustrator", "video editing",
            "content creation",

            # Other
            "report writing", "presentation skills",
            "vendor management", "inventory management",
            "quality management", "quality assurance"
        ]

        # =================================================
        # FIND SKILLS IN JOB DESCRIPTION
        # =================================================

        # Use word-aware matching instead of simple substring
        # matching. This prevents false matches such as:
        #   Java -> JavaScript
        #   C    -> C++ / C#
        #   HR   -> words that merely contain "hr"
        job_text = job_description.lower()

        for skill in skill_list:

            skill_text = skill.lower().strip()

            if not skill_text:
                continue

            # Treat letters, numbers, underscore, + and # as
            # part of a technical skill token. This is important
            # for skills such as C, C++, and C#.
            pattern = r"(?<![\w+#])" + re.escape(skill_text) + r"(?![\w+#])"

            if re.search(pattern, job_text):
                job_skills.append(skill)

        # Remove duplicates
        job_skills = list(dict.fromkeys(job_skills))

        # =================================================
        # COMPARE SAVED USER SKILLS WITH JOB SKILLS
        # =================================================

        for skill in job_skills:

            if skill.lower() in user_skills:

                matched_skills.append(skill)

            else:

                missing_skills.append(skill)

        # =================================================
        # CALCULATE MATCH PERCENTAGE
        # =================================================

        if len(job_skills) > 0:

            match_percentage = round(
                (len(matched_skills) / len(job_skills)) * 100
            )

        else:

            match_percentage = 0

    # =====================================================
    # DISPLAY PAGE
    # =====================================================

    skill_success = session.pop("skill_success", None)

    return render_template(
        "skill_analyzer.html",
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        job_skills=job_skills,
        match_percentage=match_percentage,
        saved_skills=saved_skills,
        skill_success=skill_success
    )


# -----------------------------
# Run Flask
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)