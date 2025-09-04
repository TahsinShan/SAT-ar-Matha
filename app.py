from flask import Flask, render_template, request, redirect, session, url_for, flash
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



VIDEO_UPLOAD_FOLDER = 'static/videos'
VIDEO_ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
app.config['VIDEO_UPLOAD_FOLDER'] = VIDEO_UPLOAD_FOLDER

# Create video upload folder if not exists
if not os.path.exists(VIDEO_UPLOAD_FOLDER):
    os.makedirs(VIDEO_UPLOAD_FOLDER)

def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in VIDEO_ALLOWED_EXTENSIONS







@app.route('/')
def home():
    return render_template('index.html')


from flask import flash  # make sure this is imported at the top

@app.route('/admin/add-student', methods=['GET', 'POST'])
@login_required
def add_student():
    if session.get('role') != 'admin':
        return redirect('/login')

    conn = get_db_connection()
    c = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        roll = request.form['roll']
        phone = request.form['phone']
        passcode = request.form['passcode']
        course_id = request.form['course_id']

        password_hash = generate_password_hash(passcode)

        try:
            # Insert student
            c.execute('''
                INSERT INTO users (name, role, roll, phone, password_hash)
                VALUES (?, 'student', ?, ?, ?)
            ''', (name, roll, phone, password_hash))

            student_id = c.lastrowid

            # Enroll in course
            c.execute('''
                INSERT INTO enrollments (student_id, course_id)
                VALUES (?, ?)
            ''', (student_id, course_id))

            conn.commit()
            flash("✅ Student added successfully!")
        except sqlite3.IntegrityError:
            flash("❌ Error: Student with this roll or phone already exists.")
        finally:
            conn.close()

        return redirect(url_for('add_student'))  # Reload the same page with flash message

    # GET request
    courses = c.execute("SELECT id, name, code FROM courses").fetchall()
    conn.close()
    return render_template('add_student.html', courses=courses)



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

    if user['role'] == 'student':
        conn.close()
        return render_template('student_dashboard.html', user=user, role=user['role'])

    elif user['role'] == 'admin':
        # Fetch course list for dropdown
        courses = conn.execute('SELECT id, name, code FROM courses').fetchall()
        students = conn.execute('SELECT * FROM users WHERE role = "student"').fetchall()
        conn.close()
        return render_template('admin_dashboard.html', user=user, role=user['role'], courses=courses, students=students)

    else:
        conn.close()
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
    if session.get('role') != 'admin':
        return "Unauthorized", 403


    conn = get_db_connection()
    user_id = session['user_id']
    role = session.get('role')

    courses = conn.execute("SELECT * FROM courses").fetchall()

    if request.method == 'POST':
        course_id = request.form['course_id']
        title = request.form['title']
        message = request.form['message']

        # Use teacher_id or admin_id based on role
        teacher_id = user_id

        conn.execute(
            "INSERT INTO updates (course_id, teacher_id, title, message) VALUES (?, ?, ?, ?)",
            (course_id, teacher_id, title, message)
        )

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


@app.route('/admin/edit_course/<int:course_id>', methods=['GET', 'POST'], endpoint='edit_course')
@login_required
def edit_course(course_id):
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()

    if not course:
        conn.close()
        return "Course not found", 404

    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']
        file = request.files.get('syllabus_pdf')

        syllabus_filename = course['syllabus_pdf']  # keep current file unless updated

        if file and allowed_file(file.filename):
            # Delete old file safely
            if syllabus_filename:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], syllabus_filename))
                except Exception as e:
                    print(f"Failed to remove old syllabus file: {e}")

            syllabus_filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], syllabus_filename)
            file.save(file_path)

        conn.execute('''
            UPDATE courses
            SET name = ?, code = ?, syllabus_pdf = ?
            WHERE id = ?
        ''', (name, code, syllabus_filename, course_id))

        conn.commit()
        conn.close()
        return redirect(url_for('manage_course'))

    conn.close()
    return render_template('edit_course.html', course=course)







# Check allowed files (reuse allowed_file)

@app.route('/admin/course/<int:course_id>/resources', methods=['GET', 'POST'])
@login_required
def manage_resources(course_id):
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
    if not course:
        conn.close()
        return "Course not found", 404

    if request.method == 'POST':
        title = request.form['title']
        file = request.files.get('resource_pdf')

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            conn.execute('INSERT INTO resources (course_id, filename, title) VALUES (?, ?, ?)',
                         (course_id, filename, title))
            conn.commit()
        else:
            flash("Invalid file. Only PDF allowed.")
            conn.close()
            return redirect(url_for('manage_resources', course_id=course_id))

    resources = conn.execute('SELECT * FROM resources WHERE course_id = ?', (course_id,)).fetchall()
    conn.close()
    return render_template('manage_resources.html', course=course, resources=resources)


@app.route('/admin/resource/<int:resource_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_resource(resource_id):
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    resource = conn.execute('SELECT * FROM resources WHERE id = ?', (resource_id,)).fetchone()

    if not resource:
        conn.close()
        return "Resource not found", 404

    if request.method == 'POST':
        title = request.form['title']
        file = request.files.get('resource_pdf')

        filename = resource['filename']

        if file and allowed_file(file.filename):
            # Delete old file
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except Exception as e:
                print(f"Error removing old file: {e}")

            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

        conn.execute('UPDATE resources SET title = ?, filename = ? WHERE id = ?',
                     (title, filename, resource_id))
        conn.commit()
        conn.close()
        return redirect(url_for('manage_resources', course_id=resource['course_id']))

    conn.close()
    return render_template('edit_resource.html', resource=resource)


@app.route('/admin/resource/<int:resource_id>/delete', methods=['POST'])
@login_required
def delete_resource(resource_id):
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    resource = conn.execute('SELECT * FROM resources WHERE id = ?', (resource_id,)).fetchone()

    if resource:
        # Delete file from disk
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], resource['filename']))
        except Exception as e:
            print(f"Error deleting file: {e}")

        conn.execute('DELETE FROM resources WHERE id = ?', (resource_id,))
        conn.commit()

    conn.close()
    return redirect(url_for('manage_resources', course_id=resource['course_id']))


@app.route('/resources')
@login_required
def student_resources():
    if session.get('role') != 'student':
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    student_id = session['user_id']

    # Get courses student is enrolled in
    courses = conn.execute('''
        SELECT c.id, c.name, c.code FROM courses c
        JOIN enrollments e ON e.course_id = c.id
        WHERE e.student_id = ?
    ''', (student_id,)).fetchall()

    # Get resources for these courses
    course_resources = {}
    for course in courses:
        res = conn.execute('SELECT * FROM resources WHERE course_id = ?', (course['id'],)).fetchall()
        course_resources[course['id']] = res

    conn.close()
    return render_template('student_resources.html', courses=courses, course_resources=course_resources)



@app.route('/admin/manage_resources')
@login_required
def manage_resources_list():
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    conn = get_db_connection()
    courses = conn.execute('SELECT id, name, code FROM courses').fetchall()
    conn.close()
    return render_template('manage_resources_list.html', courses=courses)




from flask import send_from_directory

@app.route('/pdf/<filename>')
@login_required
def serve_pdf(filename):
    filename = secure_filename(filename)  # sanitize filename
    uploads = app.config['UPLOAD_FOLDER']
    return send_from_directory(uploads, filename, mimetype='application/pdf', as_attachment=False)









@app.context_processor
def inject_user_role():
    return dict(role=session.get('role'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

import os

if __name__ == '__main__':
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"Endpoint: {rule.endpoint} -> URL: {rule}")
    app.run(debug=True)
