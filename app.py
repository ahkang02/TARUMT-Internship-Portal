from flask import Flask, render_template, request, redirect, url_for, flash, session
import mariadb, sys
from config import *

app = Flask(__name__)

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return render_template('sign-up.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')