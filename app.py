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

# Initialize Excel file if not present
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=['Employee Name', 'Client', 'Date', 'Session', 'Time', 'Status', 'Remarks'])
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

    new_entry = {
        'Employee Name': session['user'],
        'Client': request.form.get('client'),
        'Date': request.form.get('date'),
        'Session': request.form.get('session'),
        'Time': current_time,
        'Status': request.form.get('status'),
        'Remarks': request.form.get('remarks')
    }

    df = pd.read_excel(DATA_FILE)
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_excel(DATA_FILE, index=False)

    return redirect(url_for('employee_dashboard'))

@app.route('/log_visit', methods=['POST'])
def log_visit():
    if 'user' not in session or session.get('role') != 'employee':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json
    new_entry = {
        'Employee Name': session['user'],
        'Client': data.get('client'),
        'Date': data.get('date'),
        'Status': data.get('status'),
        'Remarks': data.get('remarks')
    }

    df = pd.read_excel(DATA_FILE)
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_excel(DATA_FILE, index=False)

    return jsonify({'message': 'Visit logged successfully'})

@app.route('/update_visit', methods=['POST'])
def update_visit():
    if 'user' not in session or session.get('role') != 'employee':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json
    required_fields = ['date', 'status']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400

    if os.path.exists(DATA_FILE):
        df = pd.read_excel(DATA_FILE)
        mask = (df['Employee Name'] == session['user']) & (df['Date'] == data['date'])

        if mask.any():
            df.loc[mask, 'Status'] = data['status']
            df.to_excel(DATA_FILE, index=False)
            return jsonify({'message': 'Visit status updated successfully'})
        else:
            return jsonify({'message': 'No matching visit found'}), 404
    else:
        return jsonify({'message': 'No data file found'}), 404

# -------------------- ADMIN FUNCTIONALITY -------------------- #

@app.route('/download_report', methods=['GET'])
def download_report():
    if 'user' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    return send_file(DATA_FILE, as_attachment=True)

# -------------------- MAIN -------------------- #

if __name__ == '__main__':
    app.run(debug=True)
