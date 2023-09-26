from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mariadb, sys
from config import *
import uuid
import json
import os
import boto3

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

@app.route('/process_company', methods=['GET'])
def process_company():
    if request.is_json:
        cur = conn.cursor()
        select_stmt = "SELECT compName, compAddress1, compAddress2 FROM Company"
        cur.execute(select_stmt)
        rows = cur.fetchall()
        cur.close()
        return jsonify(rows)

@app.route('/process_address', methods=['GET'])
def process_address():
    if request.is_json:
        cur = conn.cursor()
        select_stmt = "SELECT compAddress1, compAddress2 FROM Company WHERE compName = %s"
        cur.execute(select_stmt, (request.args.get('companyName'),))
        rows = cur.fetchone()
        cur.close()
        return jsonify(rows)

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
        insert_sql = "INSERT INTO Student VALUES (%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        try:
            cur = conn.cursor()
            cur.execute(select_stmt, (studentSupervisor,))
            rows = cur.fetchone()
            print(rows)
            cur.execute(insert_sql, (None, studFullName, studID, studIC, studGender, cohort, level, programme, studEmail, studCGPA, rows[0], studTransport, studHealthRemark, studPersonalEmail, studTermAddress, studPermanentAddress, studMobileNumber, studFixedNumber, studTechnicalSkills, studDatabaseSkills, studNetworkingSkills, None, None, tutGrp, None, None, None))
            conn.commit()
            cur.close()
        
        except mariadb.Error as e:
            print(f"Error: {e}")
            sys.exit(1)

        return redirect(url_for('login'))

    return render_template('sign-up.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if "username" in session:
        return redirect(url_for('profile'))

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
        return redirect(url_for('profile'))
    
    else:
        return render_template('login.html')
    

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop("username", None)
    return redirect(url_for('index'))

@app.route('/submitReport', methods=['GET', 'POST'])
def submitReport():

    cur = conn.cursor()
    select_stmt = "SELECT * FROM Student WHERE studEmail = %s"
    cur.execute(select_stmt, (session["username"],))
    rows = cur.fetchone()


    if request.method == 'POST':

        progressReport = request.files['progressReport']
        finalReport = request.files['finalReport']
        id = uuid.uuid4()
        progressReport_file_name_in_s3 = 'progressReport' + str(id) + "-form_files"
        finalReport_file_name_in_s3 = 'finalReport' + str(id) + "-form_files"

        s3 = boto3.resource('s3')
        try:
                print("Data inserted in MySQL RDS... uploading image to S3...")

                s3.Bucket(S3_BUCKET_NAME).put_object(Key=progressReport_file_name_in_s3, Body=progressReport)
                s3.Bucket(S3_BUCKET_NAME).put_object(Key=finalReport_file_name_in_s3, Body=finalReport)

                bucket_location = boto3.client('s3').get_bucket_location(Bucket=S3_BUCKET_NAME)
                s3_location = (bucket_location['LocationConstraint'])

                if s3_location is None:
                    s3_location = ''
                else:
                    s3_location = '-' + s3_location

                progressReport_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                    s3_location,
                    S3_BUCKET_NAME,
                    progressReport_file_name_in_s3)
                
                finalReport_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                    s3_location,
                    S3_BUCKET_NAME,
                    finalReport_file_name_in_s3)
                
                cur = conn.cursor()
                select_stmt = "SELECT formID FROM Student WHERE studEmail = %s"
                cur.execute(select_stmt, (session["username"],))
                rows = cur.fetchone()
                cur.close()

                cur = conn.cursor()
                update_stmt = "UPDATE Form SET progressReport = %s, finalReport = %s WHERE formID = %s"
                cur.execute(update_stmt, (progressReport_url, finalReport_url, rows[0]))
                cur.commit()
                cur.close()
           

        except Exception as e:
                print("Error: ", e)

    return render_template('submitReport.html', rows = rows)

@app.route('/profile', methods=['GET', 'POST'])
def profile():

    cur = conn.cursor()
    select_stmt = "SELECT * FROM Student WHERE studEmail = %s"
    cur.execute(select_stmt, (session["username"],))
    rows = cur.fetchone()

    select_stmt_sv = "SELECT * FROM Supervisor WHERE suvID = %s"
    cur.execute(select_stmt_sv, (rows[10],))
    sv_rows = cur.fetchone() 

    select_stmt_comp = "SELECT * FROM Company WHERE compID = %s"
    cur.execute(select_stmt_comp, (rows[22],))
    comp_rows = cur.fetchone()
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
        elif request.form['submit_button'] == "Submit" :

            ### Storing Company Info of a Students
            companyName = request.form['companyName']
            select_stmt = "SELECT compID FROM Company WHERE compName = %s"
            update_stmt = "UPDATE Student SET companyID = %s WHERE studEmail = %s"

            cur = conn.cursor()
            cur.execute(select_stmt, (companyName,))
            rows = cur.fetchone()
            cur.execute(update_stmt, (rows[0], session["username"]))
            conn.commit()
            cur.close()

            monthlyAllowance = request.form['monthlyAllowance']
            companySvName = request.form['comSvName']
            companySvEmail = request.form['comSvEmail']

            update_stmt = "UPDATE Student SET monthlyAllowance = %s, compSvName = %s, compSvEmail = %s WHERE studEmail = %s"

            cur = conn.cursor()
            cur.execute(update_stmt, (monthlyAllowance, companySvName, companySvEmail, session["username"]))
            conn.commit()
            cur.close()

            acceptanceForm = request.files['acceptForm']
            parentAckForm = request.files['parentAckForm']
            indemnityLetter = request.files['indemnityLetter']

            id = uuid.uuid4()
            acceptForm_file_name_in_s3 = 'acceptanceForm' + str(id) + "-form_files"
            parentAckForm_file_name_in_s3 = 'parentAckForm' + str(id) + "-form_files"
            indemnityLetter_file_name_in_s3 = 'indemnityLetter' + str(id) + "-form_files"

            s3 = boto3.resource('s3') 
            try:
                print("Data inserted in MySQL RDS... uploading image to S3...")

                s3.Bucket(S3_BUCKET_NAME).put_object(Key=acceptForm_file_name_in_s3, Body=acceptanceForm)
                s3.Bucket(S3_BUCKET_NAME).put_object(Key=parentAckForm_file_name_in_s3, Body=parentAckForm)
                s3.Bucket(S3_BUCKET_NAME).put_object(Key=indemnityLetter_file_name_in_s3, Body=indemnityLetter)

                bucket_location = boto3.client('s3').get_bucket_location(Bucket=S3_BUCKET_NAME)
                s3_location = (bucket_location['LocationConstraint'])

                if s3_location is None:
                    s3_location = ''
                else:
                    s3_location = '-' + s3_location

                accept_object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                    s3_location,
                    S3_BUCKET_NAME,
                    acceptForm_file_name_in_s3)
                
                parent_object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                    s3_location,
                    S3_BUCKET_NAME,
                    parentAckForm_file_name_in_s3)
                
                indemnity_object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                    s3_location,
                    S3_BUCKET_NAME,
                    indemnityLetter_file_name_in_s3)
                
                cur = conn.cursor()
                insert_stmt = "INSERT INTO Form Values (%s, %s, %s, %s, %s, %s)"
                cur.execute(insert_stmt, (None, parent_object_url, accept_object_url, indemnity_object_url, None, None))
                conn.commit()
                cur.close()

                cur = conn.cursor()
                select_stmt = "SELECT * FROM Form WHERE companyAcceptanceForm=%s"
                cur.execute(select_stmt, (accept_object_url,))
                rows = cur.fetchone()
                cur.close()

                cur = conn.cursor()
                update_stmt = "UPDATE Student SET formID = %s WHERE studEmail = %s"
                cur.execute(update_stmt, (rows[0], session["username"]))
                conn.commit()
                cur.close()
                
              

            except Exception as e:
                print("Error: ", e)

            return redirect(url_for('profile'))


            ## Upload To DB (File Name) -> Send To S3 (Will Do Tomorrow)

    return render_template('profile.html', rows = rows, sv_rows = sv_rows, comp_rows = comp_rows)

if __name__ == "__main__":
    app.run(debug=True)