from flask import Flask, request, jsonify, send_file, session, render_template, redirect, url_for
import pandas as pd
import os
from dotenv import load_dotenv
import ast
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

DATA_FILE = 'visit_logs.xlsx'
ISSUE_FILE = 'issue_logs.xlsx'
UPLOAD_FOLDER = 'uploads'

# Initialize Excel file if not present
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=['Employee Name', 'Client', 'Date', 'Session', 'Time', 'Status', 'Remarks', 'Photo'])
    df.to_excel(DATA_FILE, index=False)

# Load users securely from environment
USERS = ast.literal_eval(os.getenv('USERS_DICT'))

# -------------------- ROUTES -------------------- #

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = USERS.get(username.lower())
        if user and user['password'] == password:
            session['user'] = username
            session['role'] = user['role']
            if user['role'] == 'employee':
                return redirect(url_for('employee_dashboard'))
            else:
                return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/employee_dashboard')
def employee_dashboard():
    if session.get('role') == 'employee':
        return render_template('employee_dashboard.html', name=session['user'])
    return redirect(url_for('home'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') == 'admin':
        return render_template('admin_dashboard.html', name=session['user'])
    return redirect(url_for('home'))

# -------------------- EMPLOYEE FUNCTIONALITY -------------------- #

@app.route('/log_visit_form', methods=['POST'])
def log_visit_form():
    if 'user' not in session or session.get('role') != 'employee':
        return redirect(url_for('login'))

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    # Handle photo upload
    photo = request.files.get('photo')
    photo_filename = ''
    if photo:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        photo_filename = f"{session['user']}_{now.strftime('%Y%m%d%H%M%S')}.jpg"
        photo.save(os.path.join(UPLOAD_FOLDER, photo_filename))

    new_entry = {
        'Employee Name': session['user'],
        'Client': request.form.get('client'),
        'Date': request.form.get('date'),
        'Session': request.form.get('session'),
        'Time': current_time,
        'Status': request.form.get('status'),
        'Remarks': request.form.get('remarks'),
        'Photo': photo_filename
    }

    df = pd.read_excel(DATA_FILE)
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_excel(DATA_FILE, index=False)

    return redirect(url_for('employee_dashboard'))

@app.route('/submit_issue', methods=['POST'])
def submit_issue():
    if 'user' not in session or session.get('role') != 'employee':
        return redirect(url_for('login'))

    issue_text = request.form.get('issue_description')
    issue_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    issue_df = pd.DataFrame([{
        'Employee': session['user'],
        'Issue': issue_text,
        'Timestamp': issue_time
    }])

    if os.path.exists(ISSUE_FILE):
        existing = pd.read_excel(ISSUE_FILE)
        issue_df = pd.concat([existing, issue_df], ignore_index=True)

    issue_df.to_excel(ISSUE_FILE, index=False)

    return redirect(url_for('employee_dashboard'))

@app.route('/start_chat', methods=['POST'])
def start_chat():
    if 'user' not in session or session.get('role') != 'employee':
        return redirect(url_for('login'))

    query = request.form.get('chat_query')
    ai_response = f"AI Response: You asked '{query}' — This is a dummy response."

    return render_template('employee_dashboard.html', name=session['user'], ai_response=ai_response)

# -------------------- ADMIN FUNCTIONALITY -------------------- #

@app.route('/download_report', methods=['GET'])
def download_report():
    if 'user' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    return send_file(DATA_FILE, as_attachment=True)

# -------------------- MAIN -------------------- #

if __name__ == '__main__':
    app.run(debug=True)
