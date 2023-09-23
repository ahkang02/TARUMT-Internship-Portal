from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mariadb, sys
from config import *
import uuid
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# Connect to MariaDB Platform
try:
    conn = mariadb.connect(
        user = RDS_LOGIN,
        password = RDS_PASS,
        host = RDS_HOST_ENDPOINT,
        port = DB_PORT,
        database = DB_INSTANCE_NAME
    )
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)
    
# Get Cursor
cur = conn.cursor()

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/process_level', methods=['GET'])
def process_level():
    if request.is_json:
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "static/json", "LevelDataDB.json")
        data_dict = json.load(open(json_url))

        if request.args.get('level') == "Bachelor":
            return jsonify(data_dict["Bachelor"])
        elif request.args.get('level') == "Diploma":
            return jsonify(data_dict["Diploma"])

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.is_json:
        SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
        json_url = os.path.join(SITE_ROOT, "static/json", "StaffDataDB.json")
        data_dict = json.load(open(json_url))

        cur = conn.cursor()
        select_stmt = "SELECT * FROM Supervisor WHERE suvName = %s"
        cur.execute(select_stmt, (request.args.get('ucSupervisorName'),))
        rows = cur.fetchone()
        cur.close()

        return jsonify({'ucSupervisorEmail':rows[2].lower()})

    if request.method == 'POST':
        level = request.form['level']
        cohort = request.form['cohort']
        programme = request.form['programme']
        tutGrp = request.form['tutorialGrp']
        studID = request.form['studentID']
        studEmail = request.form["studentEmail"]
        studCGPA = request.form["studCGPA"]
        studentSupervisor = request.form["ucSupervisor"]
        studFullName = request.form["studentFullName"]
        studIC = request.form["studIC"]
        studGender = request.form["studGender"]
        studTransport = request.form["studTransport"]
        studHealthRemark = request.form["studHealthRemark"]
        studPersonalEmail = request.form["studPersonalEmail"]
        studTermAddress = request.form["studTermAddress"]
        studPermanentAddress = request.form["studPermanentAddress"]
        studMobileNumber = request.form["studMobileNumber"]
        studFixedNumber = request.form["studFixedNumber"]
        studTechnicalSkills = request.form["studTechnicalSkills"]
        studDatabaseSkills = request.form["studDatabaseSkills"]
        studNetworkingSkills = request.form["studNetworkingSkills"]

        select_stmt = "SELECT suvID FROM Supervisor WHERE suvName = %s"
        insert_sql = "INSERT INTO Student VALUES (%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s, %s, %s, %s)"
        try:
            cur = conn.cursor()
            cur.execute(select_stmt, (studentSupervisor,))
            rows = cur.fetchone()
            print(rows)
            cur.execute(insert_sql, (None, studFullName, studID, studIC, studGender, cohort, level, programme, studEmail, studCGPA, rows[0], studTransport, studHealthRemark, studPersonalEmail, studTermAddress, studPermanentAddress, studMobileNumber, studFixedNumber, studTechnicalSkills, studDatabaseSkills, studNetworkingSkills, None, None, tutGrp))
            conn.commit()
            cur.close()
        
        except mariadb.Error as e:
            print(f"Error: {e}")
            sys.exit(1)

        return redirect(url_for('login'))

    return render_template('sign-up.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            select_stmt = "SELECT * FROM Student WHERE studEmail = %s"
            cur.execute(select_stmt, (username,))
            rows = cur.fetchone()
            cur.close()
        except mariadb.Error as e:
            print(f"Error: {e}")

        if username == rows[8] and password == rows[3]:
            session["username"] = username
            print(session["username"])
        return redirect(url_for('profile'))
    
    else:
        if "user" in session:
            return redirect(url_for('profile'))
    return render_template('login.html')
    

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop("username", None)
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    cur = conn.cursor()
    select_stmt = "SELECT * FROM Student WHERE studEmail = %s"
    cur.execute(select_stmt, (session["username"],))
    rows = cur.fetchone()

    select_stmt_sv = "SELECT * FROM Supervisor WHERE suvID = %s"
    cur.execute(select_stmt_sv, (rows[10],))
    sv_rows = cur.fetchone()

    cur.close()

    if request.is_json:
        cur = conn.cursor()
        select_stmt = "SELECT * FROM Supervisor WHERE suvName = %s"
        cur.execute(select_stmt, (request.args.get('ucSupervisorName'),))
        rows = cur.fetchone()
        cur.close()

        return jsonify({'ucSupervisorEmail':rows[2].lower()})

    if request.method == 'POST':
        if request.form['submit_button'] == 'Update':
            print("Hello I'M HERE")
            ucSupervisorName = request.form['ucSupervisorName1']

            update_stmt = "UPDATE Student SET studSv = %s WHERE studEmail = %s"
            select_stmt = "SELECT suvID FROM Supervisor WHERE suvName = %s"
            cur = conn.cursor()
            cur.execute(select_stmt, (ucSupervisorName,))
            rows = cur.fetchone()
            cur.execute(update_stmt, (rows[0], session["username"]))
            conn.commit()
            cur.close()

            return redirect(url_for('profile'))

            ## Retrieve Info Then Update DB (Will Do Tomorrow)
        elif request.form['submit_button'] == "Save & Submit" :
            acceptanceForm = request.files['acceptanceForm"']
            parentAckForm = request.files['parentAckForm']
            indemnityLetter = request.files['indemnityLetter']
            hiredEvidence = request.files['hiredEvidence']

            ## Upload To DB (File Name) -> Send To S3 (Will Do Tomorrow)

    return render_template('profile.html', rows = rows, sv_rows = sv_rows)

if __name__ == "__main__":
    app.run(debug=True)