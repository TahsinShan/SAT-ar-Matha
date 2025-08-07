from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if not exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app.secret_key = 'super-secret-key'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        id_num = request.form['id_num']
        roll = request.form.get('roll')
        reg_no = request.form.get('reg_no')
        phone = request.form['phone']
        password = generate_password_hash(request.form['password'])

        # Prevent signup as admin
        if role == 'admin':
            return "Admin signup is not allowed!"

        conn = get_db_connection()
        conn.execute('INSERT INTO users (name, role, id_num, roll, reg_no, phone, password_hash) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (name, role, id_num, roll, reg_no, phone, password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE phone = ?', (phone,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            return "Invalid Credentials!"

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()

    if user['role'] == 'student':
        return render_template('student_dashboard.html', user=user, role=user['role'])
    elif user['role'] == 'teacher':
        return render_template('teacher_dashboard.html', user=user, role=user['role'])
    elif user['role'] == 'admin':
        return render_template('admin_dashboard.html', user=user, role=user['role'])
    else:
        return "Invalid role!"

# Manage Courses (Add & List) for Admin
@app.route('/admin/manage_course', methods=['GET', 'POST'])
@login_required
def manage_course():
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))

    conn = get_db_connection()

    if request.method == 'POST':
        # Handle adding new course
        name = request.form['name']
        code = request.form['code']
        file = request.files['syllabus_pdf']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            conn.execute('INSERT INTO courses (name, code, syllabus_pdf) VALUES (?, ?, ?)',
                         (name, code, filename))
            conn.commit()
        else:
            conn.close()
            return "Invalid file. Only PDF allowed."

    courses = conn.execute('SELECT * FROM courses').fetchall()
    conn.close()
    return render_template('manage_course.html', courses=courses, role='admin')

# Delete Course route
@app.route('/admin/delete_course/<int:course_id>', methods=['POST'])
@login_required
def delete_course(course_id):
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    if course:
        # Optionally delete the PDF file from server
        if course['syllabus_pdf']:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], course['syllabus_pdf']))
            except Exception:
                pass

        conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
        conn.commit()

    conn.close()
    return redirect(url_for('manage_course'))

@app.route('/courses')
def course_list():
    conn = get_db_connection()
    courses = conn.execute('SELECT * FROM courses').fetchall()
    conn.close()
    return render_template('course_list.html', courses=courses)


@app.route('/student/enroll', methods=['GET', 'POST'])
@login_required
def enroll_courses():
    if session.get('role') != 'student':
        return redirect(url_for('dashboard'))

    conn = get_db_connection()

    if request.method == 'POST':
        selected_courses = request.form.getlist('courses')
        student_id = session['user_id']

        # Remove old enrollments (optional, to reset)
        conn.execute('DELETE FROM enrollments WHERE student_id = ?', (student_id,))

        # Add new enrollments
        for course_id in selected_courses:
            conn.execute('INSERT OR IGNORE INTO enrollments (student_id, course_id) VALUES (?, ?)', (student_id, course_id))

        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    # GET method: show courses with checkbox, pre-check enrolled courses
    courses = conn.execute('SELECT * FROM courses').fetchall()
    enrolled_courses = conn.execute('SELECT course_id FROM enrollments WHERE student_id = ?', (session['user_id'],)).fetchall()
    conn.close()

    enrolled_ids = {row['course_id'] for row in enrolled_courses}

    return render_template('enroll_courses.html', courses=courses, enrolled_ids=enrolled_ids)


@app.route('/upload_update', methods=['GET', 'POST'])
@login_required
def upload_update():
    if session.get('role') != 'teacher':
        return "Unauthorized", 403

    conn = get_db_connection()
    teacher_id = session['user_id']
    courses = conn.execute("SELECT * FROM courses").fetchall()

    if request.method == 'POST':
        course_id = request.form['course_id']
        title = request.form['title']
        message = request.form['message']
        conn.execute("INSERT INTO updates (course_id, teacher_id, title, message) VALUES (?, ?, ?, ?)",
                    (course_id, teacher_id, title, message))

        conn.commit()
        conn.close()
        return redirect(url_for('updates'))

    conn.close()
    return render_template('upload_update.html', courses=courses)


@app.route('/updates')
@login_required
def updates():
    conn = get_db_connection()
    c = conn.cursor()

    role = session.get('role')
    user_id = session.get('user_id')

    if role == 'student':
        # Only show updates from courses the student is enrolled in
        c.execute('''
            SELECT updates.id, updates.message, updates.created_at, updates.teacher_id,
                   users.name, updates.title
            FROM updates
            JOIN users ON updates.teacher_id = users.id
            JOIN enrollments ON enrollments.course_id = updates.course_id
            WHERE enrollments.student_id = ?
            ORDER BY updates.created_at DESC
        ''', (user_id,))
    else:
        # Admin or teacher can see all updates
        c.execute('''
            SELECT updates.id, updates.message, updates.created_at, updates.teacher_id,
                   users.name, updates.title
            FROM updates
            JOIN users ON updates.teacher_id = users.id
            ORDER BY updates.created_at DESC
        ''')

    updates = c.fetchall()
    conn.close()

    return render_template('updates.html', updates=updates)



@app.route('/manage-events', methods=['GET', 'POST'])
@login_required
def manage_events():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        event_date = request.form['event_date']
        conn.execute('INSERT INTO events (title, description, event_date) VALUES (?, ?, ?)',
                     (title, description, event_date))
        conn.commit()

    events = conn.execute('SELECT * FROM events ORDER BY event_date DESC').fetchall()
    conn.close()
    return render_template('manage_events.html', events=events)


@app.route('/delete-event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    conn.execute('DELETE FROM events WHERE id = ?', (event_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('manage_events'))


@app.route('/events')
@login_required
def events():
    conn = get_db_connection()
    events = conn.execute('SELECT * FROM events ORDER BY event_date DESC').fetchall()
    conn.close()
    return render_template('events.html', events=events)


@app.route('/manage-users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        # Delete user
        user_id = request.form.get('user_id')
        if user_id:
            # Prevent deleting admin users if you want (optional)
            user = conn.execute('SELECT role FROM users WHERE id = ?', (user_id,)).fetchone()
            if user and user['role'] != 'admin':
                conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
                conn.commit()
        conn.close()
        return redirect(url_for('manage_users'))
    
    users = conn.execute('SELECT id, name, role, phone FROM users ORDER BY role, name').fetchall()
    conn.close()
    
    return render_template('manage_users.html', users=users)




@app.route('/delete-update/<int:update_id>', methods=['POST'])
@login_required
def delete_update(update_id):
    conn = get_db_connection()
    update = conn.execute('SELECT * FROM updates WHERE id = ?', (update_id,)).fetchone()

    if not update:
        conn.close()
        return "Update not found", 404

    user_id = session.get('user_id')
    role = session.get('role')

    # Only allow if admin or owner
    if role == 'admin' or (role == 'teacher' and update['teacher_id'] == user_id):
        conn.execute('DELETE FROM updates WHERE id = ?', (update_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('updates'))
    else:
        conn.close()
        return "Unauthorized", 403






@app.context_processor
def inject_user_role():
    return dict(role=session.get('role'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

import os

if __name__ == '__main__':
    if os.environ.get('FLASK_ENV') != 'production':
        app.run(debug=True)
