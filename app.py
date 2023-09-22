from flask import Flask, render_template, request, redirect, url_for, flash, session
import mariadb, sys
from config import *
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# Connect to MariaDB Platform
# try:
#    conn = mariadb.connect(
#        user = RDS_LOGIN,
#        password = RDS_PASS,
#        host = RDS_HOST_ENDPOINT,
#        port = DB_PORT,
#        database = DB_INSTANCE_NAME
#    )
# except mariadb.Error as e:
#    print(f"Error connecting to MariaDB Platform: {e}")
#    sys.exit(1)
    
# Get Cursor
# cur = conn.cursor()

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':
        level = request.form['level']
        cohort = request.form['cohort']
        programme = request.form['programme']
        tutGrp = request.form['tutorialGrp']
        studID = request.form['studentID']
        studEmail = request.form["studentEmail"]
        studentSupervisor = request.form["ucSupervisor"]
        studentSuperEmail = request.form["ucSupervisorEmail"]
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

        insert_sql = "INSERT INTO STUDENTS VALUES (%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s)"
        return redirect(url_for('login'))

    return render_template('sign-up.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        session["username"] = username

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
    return render_template('profile.html')

if __name__ == "__main__":
    app.run(debug=True)