from flask import Flask, render_template, request, redirect
import mysql.connector
import os
app = Flask(__name__)

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv("DB_PASSWORD"),
    database="student_attendance"
)

cursor = db.cursor(dictionary=True)


# ---------------- HOME / DASHBOARD ----------------
@app.route("/")
def index():

    # Total students
    cursor.execute("SELECT COUNT(*) AS total FROM students")
    total_students = cursor.fetchone()["total"]

    # Present today
    cursor.execute("""
        SELECT COUNT(*) AS present
        FROM attendance
        WHERE attendance_date = CURDATE()
        AND status = 'Present'
    """)
    present_today = cursor.fetchone()["present"]

    # Absent today
    cursor.execute("""
        SELECT COUNT(*) AS absent
        FROM attendance
        WHERE attendance_date = CURDATE()
        AND status = 'Absent'
    """)
    absent_today = cursor.fetchone()["absent"]

    return render_template(
        "index.html",
        total_students=total_students,
        present_today=present_today,
        absent_today=absent_today
    )


# ---------------- ADD STUDENT ----------------
@app.route("/add-student", methods=["GET", "POST"])
def add_student():

    if request.method == "POST":

        name = request.form["name"]
        roll_no = request.form["roll_no"]
        department = request.form["department"]
        year = request.form["year"]

        sql = """
            INSERT INTO students
            (name, roll_no, department, year)
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            sql,
            (name, roll_no, department, year)
        )

        db.commit()

        return redirect("/")


    return render_template("add_student.html")


# ---------------- MARK ATTENDANCE ----------------
@app.route("/mark-attendance", methods=["GET", "POST"])
def mark_attendance():

    if request.method == "POST":

        student_id = request.form["student_id"]
        status = request.form["status"]
        # Check duplicate attendance
        cursor.execute(
            """
            SELECT id FROM attendance
            WHERE student_id = %s
            AND attendance_date = CURDATE()
            """,
            (student_id,)
        )

        existing = cursor.fetchone()

        if existing:
            return "Attendance already marked for today."

        sql = """
            INSERT INTO attendance
            (student_id, attendance_date, status)
            VALUES (%s, CURDATE(), %s)
        """

        cursor.execute(
            sql,
            (student_id, status)
        )

        db.commit()

        return redirect("/")


    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    return render_template(
        "mark_attendance.html",
        students=students
    )
# ---------------- VIEW ATTENDANCE ----------------
@app.route("/view-attendance")
def view_attendance():

    selected_date = request.args.get("date")

    if selected_date:

        sql = """
            SELECT
                attendance.id,
                students.name,
                students.roll_no,
                students.department,
                students.year,
                attendance.attendance_date,
                attendance.status
            FROM attendance
            JOIN students
            ON attendance.student_id = students.id
            WHERE attendance.attendance_date = %s
            ORDER BY attendance.id DESC
        """

        cursor.execute(sql, (selected_date,))

    else:

        sql = """
            SELECT
                attendance.id,
                students.name,
                students.roll_no,
                students.department,
                students.year,
                attendance.attendance_date,
                attendance.status
            FROM attendance
            JOIN students
            ON attendance.student_id = students.id
            ORDER BY attendance.attendance_date DESC
        """

        cursor.execute(sql)

    attendance = cursor.fetchall()

    # Attendance summary
    total_records = len(attendance)

    total_present = sum(
        1 for row in attendance
        if row["status"] == "Present"
    )

    total_absent = sum(
        1 for row in attendance
        if row["status"] == "Absent"
    )

    return render_template(
        "view_attendance.html",
        attendance=attendance,
        selected_date=selected_date,
        total_records=total_records,
        total_present=total_present,
        total_absent=total_absent
    )
# ---------------- EDIT STUDENT ----------------
@app.route("/edit-student/<int:id>", methods=["GET", "POST"])
def edit_student(id):

    if request.method == "POST":

        name = request.form["name"]
        roll_no = request.form["roll_no"]
        department = request.form["department"]
        year = request.form["year"]

        sql = """
            UPDATE students
            SET name=%s,
                roll_no=%s,
                department=%s,
                year=%s
            WHERE id=%s
        """

        cursor.execute(
            sql,
            (name, roll_no, department, year, id)
        )

        db.commit()

        return redirect("/")

    cursor.execute(
        "SELECT * FROM students WHERE id=%s",
        (id,)
    )

    student = cursor.fetchone()

    return render_template(
        "edit_student.html",
        student=student
    )

    
  
# ---------------- STUDENT MANAGEMENT ----------------
@app.route("/students")
def students():

    cursor.execute("SELECT * FROM students ORDER BY id DESC")
    students = cursor.fetchall()

    return render_template(
        "students.html",
        students=students
    )
    # ---------------- DELETE STUDENT ----------------
@app.route("/delete-student/<int:id>")
def delete_student(id):

    # First delete attendance records
    cursor.execute(
        "DELETE FROM attendance WHERE student_id = %s",
        (id,)
    )

    # Then delete student
    cursor.execute(
        "DELETE FROM students WHERE id = %s",
        (id,)
    )

    db.commit()

    return redirect("/students")
    # ---------------- STUDENT DETAILS ----------------
@app.route("/student-details/<int:id>")
def student_details(id):

    cursor.execute(
        "SELECT * FROM students WHERE id = %s",
        (id,)
    )

    student = cursor.fetchone()

    return render_template(
        "student_details.html",
        student=student
    )
    # ---------------- ATTENDANCE REPORT ----------------
@app.route("/attendance-report")
def attendance_report():

    sql = """
        SELECT
            students.id,
            students.name,
            students.roll_no,
            students.department,
            students.year,

            COUNT(attendance.id) AS total_days,

            SUM(
                CASE
                    WHEN attendance.status = 'Present' THEN 1
                    ELSE 0
                END
            ) AS present_days,

            SUM(
                CASE
                    WHEN attendance.status = 'Absent' THEN 1
                    ELSE 0
                END
            ) AS absent_days

        FROM students

        LEFT JOIN attendance
        ON students.id = attendance.student_id

        GROUP BY
            students.id,
            students.name,
            students.roll_no,
            students.department,
            students.year

        ORDER BY students.id DESC
    """

    cursor.execute(sql)
    students = cursor.fetchall()

    for student in students:

        if student["total_days"] > 0:
            student["percentage"] = round(
                (student["present_days"] / student["total_days"]) * 100,
                2
            )
        else:
            student["percentage"] = 0

    return render_template(
        "attendance_report.html",
        students=students
    )
    
# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
  
  