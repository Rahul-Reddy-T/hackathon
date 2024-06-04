from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask import request, jsonify


app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.debug = True

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx'}
db = SQLAlchemy(app)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'teacher' or 'student'

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    subject_code = db.Column(db.String(100))

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100))
    semester = db.Column(db.String(10))
    subject = db.Column(db.String(100))
    details = db.Column(db.Text)

# Utility function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Routes
@app.route("/")
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        session['user_role'] = user.role
        if user.role == 'teacher':
            return redirect(url_for('teacher_home'))
        else:
            return redirect(url_for('student_home'))
    else:
        flash('Invalid email or password')
        return redirect(url_for('index'))

@app.route('/teacher')
def teacher_home():
    if 'user_id' not in session or session['user_role'] != 'teacher':
        return redirect(url_for('index'))
    return render_template('teacher_home.html')

@app.route('/student_home', methods=['GET'])
def student_home():
    if 'user_id' not in session or session['user_role'] != 'student':
        return redirect(url_for('index'))

    semester = request.args.get('semester')
    subject = request.args.get('subject')
    subject_code = request.args.get('subject_code')

    query = Book.query

    if semester:
        query = query.filter_by(semester=semester)
    if subject:
        query = query.filter(Book.subject.ilike(f'%{subject}%'))
    if subject_code:
        query = query.filter(Book.subject_code.ilike(f'%{subject_code}%'))

    books = query.all()

    return render_template('home.html', books=books)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session or session['user_role'] != 'teacher':
        return redirect(url_for('index'))

    if 'file' not in request.files:
        return redirect(url_for('teacher_home'))

    file = request.files['file']
    semester = request.form['semester']
    subject = request.form['subject']
    subject_code = request.form['subject_code']

    if file.filename == '':
        return redirect(url_for('teacher_home'))

    if file and allowed_file(file.filename):
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Save file info to database
        book = Book(filename=filename, semester=int(semester), subject=subject, subject_code = subject_code)

        db.session.add(book)
        db.session.commit()

        return redirect(url_for('teacher_home'))

    return redirect(url_for('teacher_home'))

@app.route('/request_resource')
def request_resource():
    return render_template('request_resource.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/submit_request', methods=['POST'])
def submit_request():
    if request.method == 'POST':
        student_name = request.form.get('studentName')
        semester = request.form.get('semester')
        subject = request.form.get('subject')
        details = request.form.get('details')

        # Create a new entry in the database
        new_request = Request(student_name=student_name, semester=semester, subject=subject, details=details)
        db.session.add(new_request)
        db.session.commit()

        return jsonify({'message': 'Request submitted successfully'}), 201


@app.route('/teacher_dashboard')
def teacher_dashboard():
    # Retrieve all submitted requests from the database
    requests = Request.query.all()
    return render_template('teacher_dashboard.html', requests=requests)


if __name__ == '__main__':
    app.run(debug=True)
