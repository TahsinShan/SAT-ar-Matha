import sqlite3
from werkzeug.security import generate_password_hash

# Connect to DB
conn = sqlite3.connect('database.db')
c = conn.cursor()

# Users Table
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        id_num TEXT,
        roll TEXT,
        reg_no TEXT,
        photo TEXT,
        phone TEXT,
        password_hash TEXT NOT NULL
    )
''')

# Courses Table
c.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT NOT NULL,
        syllabus_pdf TEXT
    )
''')

# Enrollments Table
c.execute('''
    CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        UNIQUE(student_id, course_id),
        FOREIGN KEY(student_id) REFERENCES users(id),
        FOREIGN KEY(course_id) REFERENCES courses(id)
    )
''')

# Schedule Updates Table
c.execute('''
    CREATE TABLE IF NOT EXISTS schedule_updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,
        new_date TEXT NOT NULL,
        new_time TEXT NOT NULL,
        message TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(course_id) REFERENCES courses(id),
        FOREIGN KEY(teacher_id) REFERENCES users(id)
    )
''')

# Updates Table
c.execute('''
    CREATE TABLE IF NOT EXISTS updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        teacher_id INTEGER,
        title TEXT NOT NULL,
        message TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(course_id) REFERENCES courses(id),
        FOREIGN KEY(teacher_id) REFERENCES users(id)
    )
''')

# Test Reports Table
c.execute('''
    CREATE TABLE IF NOT EXISTS test_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        student_id INTEGER,
        marks INTEGER,
        report_pdf TEXT,
        FOREIGN KEY(course_id) REFERENCES courses(id),
        FOREIGN KEY(student_id) REFERENCES users(id)
    )
''')

# Events Table (updated column name to event_date)
c.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        created_by INTEGER,
        event_date TEXT,
        FOREIGN KEY(created_by) REFERENCES users(id)
    )
''')

# Notifications Table
c.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT,
        created_at TEXT,
        for_role TEXT
    )
''')

# Insert Default Admins if not exists
admin_users = [
    ('Admin One', 'admin', None, None, None, None, '01700000001', generate_password_hash('abcd1234')),
    ('Admin Two', 'admin', None, None, None, None, '01700000002', generate_password_hash('abcd1234')),
    ('Admin Three', 'admin', None, None, None, None, '01700000003', generate_password_hash('abcd1234')),
    ('Admin Four', 'admin', None, None, None, None, '01700000004', generate_password_hash('abcd1234')),
    ('Admin Five', 'admin', None, None, None, None, '01700000005', generate_password_hash('abcd1234')),
    ('Admin Six', 'admin', None, None, None, None, '01700000006', generate_password_hash('abcd1234'))
]

existing_admins = c.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
if existing_admins == 0:
    c.executemany(
        'INSERT INTO users (name, role, id_num, roll, reg_no, photo, phone, password_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        admin_users
    )

# Commit and Close
conn.commit()
conn.close()

print("Database Initialized!")
