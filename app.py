from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sys
import pymysql
from pymysql import connections
from config import *
import uuid
import json
import os
import boto3

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['ADMIN_CREDENTIAL'] = 'admin'

# Connect to MariaDB Platform
try:
    conn = connections.Connection(
        host = RDS_HOST_ENDPOINT,
        port = DB_PORT,
        user = RDS_LOGIN,
        password = RDS_PASS,
        db = DB_INSTANCE_NAME
    )
except pymysql.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)
    
# Get Cursor
cur = conn.cursor()

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' in session and 'admin' in session and session.get('username') == app.config['ADMIN_CREDENTIAL'] and session.get('admin') == True:
        return redirect(url_for('studentsListing', page_num=1))

    print(session.get('username'))
    print(session.get('admin'))
    return render_template('index.html')

### Processing AJAX Request ###
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
        select_stmt = "SELECT compName, compAddress1, compAddress2 FROM Company WHERE status = %s"
        cur.execute(select_stmt, (1,))
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
    
### Sign Up Starts Here ###
@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if 'username' in session and 'admin' in session:
        return redirect(url_for('index'))
    
    cur = conn.cursor()
    select_stmt = "SELECT * FROM Supervisor"
    cur.execute(select_stmt)
    sv_rows = cur.fetchall()
    cur.close()

    if request.is_json:
        cur = conn.cursor()
        select_stmt = "SELECT * FROM Supervisor WHERE suvName = %s"
        cur.execute(select_stmt, (request.args.get('ucSupervisorName'),))
        rows = cur.fetchone()
        cur.close()

        return jsonify({'ucSupervisorEmail':rows[2].lower()})

    if request.method == 'POST':
        if request.form['submit_button'] == 'I Accept':
            level = request.form['level']
            cohort = request.form['cohort']
            programme = request.form['programme']
            tutGrp = request.form['tutorialGrp']
            studID = request.form['studentID']
            studEmail = request.form["studentEmail"]
            studCGPA = request.form["studCGPA"]
            studentSupervisor = request.form["ucSupervisor"]
            studFullName = request.form["studentFullName"].title()
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
            
            except pymysql.Error as e:
                print(f"Error: {e}")
                sys.exit(1)

            return redirect(url_for('login'))
        elif request.form['submit_button'] == 'I Decline':
            return redirect(url_for('index'))
        elif request.form['submit_button'] == 'Company Registration':
            
            companyName = request.form['companyName']
            companyAddress1 = request.form['companyAddress1']
            companyAddress2 = request.form['companyAddress2']
            insert_stmt = "INSERT INTO Company VALUES (%s, %s, %s, %s, %s)"
            try:
                cur = conn.cursor()
                cur.execute(insert_stmt, (None, companyName, companyAddress1, companyAddress2, 0))
                conn.commit()
                cur.close()
            
            except pymysql.Error as e:
                print(f"Error: {e}")
                sys.exit(1)
            
            return render_template('login.html')

    return render_template('sign-up.html', sv_rows = sv_rows)

### Login Starts Here ###
@app.route('/login', methods=['GET', 'POST'])
def login():

    if 'username' in session and 'admin' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        rows = None 
        cur = conn.cursor()

        if username == app.config['ADMIN_CREDENTIAL'] and password == app.config['ADMIN_CREDENTIAL']:
            session['username'] = username
            session['admin'] = True
            return redirect(url_for('studentsListing', page_num = 1))
        else:
            try:
                select_stmt = "SELECT * FROM Student WHERE studEmail = %s"
                cur.execute(select_stmt, (username,))
                rows = cur.fetchone()
                cur.close()
            except pymysql.Error as e:
                print(f"Error: {e}")

            if rows is not None and password == rows[3]:
                session["username"] = username
                session['admin'] = False
                return redirect(url_for('profile'))
            else:
                print('enter invalid')
                error_msg = "Invalid Username or Password"
                return render_template('login.html', error_msg = error_msg)
    else:
        if "username" in session:
            return redirect(url_for('profile'))
        return render_template('login.html')
    
### Logout Starts Here ###
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop("username", None)
    session.pop("admin", None)
    return redirect(url_for('index'))

### Submit Progress Report / Final Report Starts Here ###
@app.route('/submitReport', methods=['GET', 'POST'])
def submitReport():

    if 'username' in session and 'admin' in session and session.get('username') == app.config['ADMIN_CREDENTIAL'] and session.get('admin') == True:
        return redirect(url_for('studentsListing', page_num=1))
    elif 'username' not in session and 'admin' not in session:
        return redirect(url_for('index'))

     
    cur = conn.cursor()
    select_stmt = "SELECT * FROM Student WHERE studEmail = %s"
    cur.execute(select_stmt, (session["username"],))
    rows = cur.fetchone()
    cur.close()


    if request.method == 'POST':

        progressReport = request.files['progressReport']
        finalReport = request.files['finalReport']
        progressExtension = progressReport.filename.split(".")[1]
        finalExtension = finalReport.filename.split(".")[1]
        id = uuid.uuid4()
        progressReport_file_name_in_s3 = 'progressReport' + str(id) + "." + progressExtension
        finalReport_file_name_in_s3 = 'finalReport' + str(id) + "." + finalExtension

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

### User Profile Starts Here ###
@app.route('/profile', methods=['GET', 'POST'])
def profile():

    if 'username' in session and 'admin' in session and session.get('username') == app.config['ADMIN_CREDENTIAL'] and session.get('admin') == True:
        return redirect(url_for('studentsListing', page_num=1))
    elif 'username' not in session and 'admin' not in session:
        return redirect(url_for('index'))
    
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

            ### Storing Company Info of Students
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

            ### Storing Forms Starts Here
            acceptanceForm = request.files['acceptForm']
            parentAckForm = request.files['parentAckForm']
            indemnityLetter = request.files['indemnityLetter']

            ### Setting Random IDs to the Files
            id = uuid.uuid4()
            acceptanecFormExtension = acceptanceForm.filename.split(".")[1]
            parentAckFormExtension = parentAckForm.filename.split(".")[1]
            indemnityLetterExtension = indemnityLetter.filename.split(".")[1]

            acceptForm_file_name_in_s3 = 'acceptanceForm' + str(id) + "." + acceptanecFormExtension
            parentAckForm_file_name_in_s3 = 'parentAckForm' + str(id) + "." + parentAckFormExtension
            indemnityLetter_file_name_in_s3 = 'indemnityLetter' + str(id) + "." + indemnityLetterExtension

            ### Calling S3 Bucket API
            s3 = boto3.resource('s3') 
            try:

                ### Upload to S3 Bucket Starts Here
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
                
                ### Storing Forms Info & Updating Students Form ID Starts Here
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

    return render_template('profile.html', rows = rows, sv_rows = sv_rows, comp_rows = comp_rows)

@app.route('/studentsListing/<int:page_num>')
def studentsListing(page_num):
    if 'username' not in session or 'admin' not in session or session.get('username') != app.config['ADMIN_CREDENTIAL'] or session.get('admin') == False:
        return redirect(url_for('index'))
     
    per_page = 10
    offset = (page_num - 1) * per_page
    
    query = request.args.get('query') 
    if query:
        cur = conn.cursor()
        studs = "SELECT studIDCardNum, studName FROM Student WHERE studName LIKE %s ORDER BY studID, studName LIMIT %s OFFSET %s"
        cur.execute(studs, ('%' + query + '%', per_page, offset))
        rows = cur.fetchall()
        cur.close()
        #get total number of records
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM Student WHERE studName LIKE %s", ('%' + query + '%',))
        total_records = cur.fetchone()[0]
        cur.close()
    else:
        query=""
        cur = conn.cursor()
        studs = "SELECT studIDCardNum, studName FROM Student ORDER BY studID, studName LIMIT %s OFFSET %s"
        cur.execute(studs, (per_page, offset))
        rows = cur.fetchall()
        cur.close()
        #get total number of records
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM Student")
        total_records = cur.fetchone()[0]
        cur.close()

    total_pages = (total_records + per_page - 1) // per_page

    return render_template('students-listing.html', rows=rows, page_num=page_num, total_pages=total_pages, query=query)

@app.route('/studentDetails', methods=['GET'])
def studentDetails():
    if 'username' not in session or 'admin' not in session or session.get('username') != app.config['ADMIN_CREDENTIAL'] or session.get('admin') == False:
        return redirect(url_for('index'))       

    studID = request.args.get('studID')

    if studID:
        cur = conn.cursor()
        select_stmt = "SELECT * FROM Student WHERE studIDCardNum = %s"
        cur.execute(select_stmt, (studID,))
        rows = cur.fetchone()

        select_stmt_sv = "SELECT * FROM Supervisor WHERE suvID = %s"
        cur.execute(select_stmt_sv, (rows[10],))
        sv_rows = cur.fetchone() 

        select_stmt_comp = "SELECT * FROM Company WHERE compID = %s"
        cur.execute(select_stmt_comp, (rows[22],))
        comp_rows = cur.fetchone()

        select_stmt_form = "SELECT * FROM Form WHERE formID = %s"
        cur.execute(select_stmt_form, (rows[21],))
        form_rows = cur.fetchone()
        cur.close()

    else:
        return redirect(url_for('studentsListing', page_num=1))

    return render_template('student-details.html', rows = rows, sv_rows = sv_rows, comp_rows = comp_rows, form_rows = form_rows)

@app.route('/deleteStud', methods=['GET'])
def deleteStud():
    studID = request.args.get('studID')
    cur = conn.cursor()
    delete_query = "DELETE FROM Student WHERE studIDCardNum = %s"
    cur.execute(delete_query, (studID,))
    conn.commit()
    cur.close()
    return jsonify({'message': 'Student deleted successfully'})

@app.route('/companyListing/<int:page_num>')
def companyListing(page_num):
    if 'username' not in session or 'admin' not in session or session.get('username') != app.config['ADMIN_CREDENTIAL'] or session.get('admin') == False:
        return redirect(url_for('index'))
    
    per_page = 10 
    offset = (page_num - 1) * per_page

    query = request.args.get('query') 
    if query:
        cur = conn.cursor()
        comp = "SELECT * FROM Company  WHERE compName LIKE %s ORDER BY status, compName LIMIT %s OFFSET %s"
        cur.execute(comp, ('%' + query + '%',per_page, offset))
        rows = cur.fetchall()
        cur.close()
        #get total number of records
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM Company WHERE compName LIKE %s", ('%' + query + '%',))
        total_records_company = cur.fetchone()[0]
        cur.close()
    else:
        query=""
        cur = conn.cursor()
        comp = "SELECT * FROM Company ORDER BY status, compName  LIMIT %s OFFSET %s"
        cur.execute(comp, (per_page, offset))
        rows = cur.fetchall()
        cur.close()
        #get total number of records
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM Company")
        total_records_company = cur.fetchone()[0]
        cur.close()

    total_pages_company = (total_records_company + per_page - 1) // per_page

    return render_template('company-listing.html', rows=rows, page_num=page_num, total_pages=total_pages_company, query=query)

@app.route('/deleteComp', methods=['GET'])
def deleteComp():
    compID = request.args.get('compID')
    cur = conn.cursor()
    delete_query = "DELETE FROM Company WHERE compID = %s"
    cur.execute(delete_query, (compID,))
    conn.commit()
    cur.close()
    return jsonify({'message': 'Company deleted successfully'})

@app.route('/updateCompStatus', methods=['GET'])
def updateCompStatus():
    compID = request.args.get('compID')
    status = request.args.get('status')
    cur = conn.cursor()
    delete_query = "UPDATE Company SET status = %s WHERE compID = %s"
    cur.execute(delete_query, (status, compID,))
    conn.commit()
    cur.close()
    return jsonify({'message': 'Company updated successfully'})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)