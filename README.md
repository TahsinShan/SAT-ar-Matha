# Uniportal – A University Portal That Doesn’t Suck

**Uniportal** is a lightweight, Flask-based web app that brings your university experience into the modern age. Whether you're a student, teacher, or admin, this portal keeps things organized, smooth, and—dare we say—actually usable.

---

## What is This?

Uniportal is your personal DIY university system. Think of it as your escape route from boring institutional websites. It’s designed to help students keep up with rescheduled lectures, view course info and test reports, and let teachers/admins manage it all through a clean web interface.

It’s not trying to be fancy. It’s trying to be useful. And a little fun.

---

## Key Features

- Student and Teacher registration and login
- Admin dashboard with course and event management
- Class rescheduling announcements by teachers
- Students can enroll in courses and only see relevant updates
- File uploads for PDFs like syllabi or test reports
- Role-based access for Students, Teachers, and Admins
- Simple point and request system (under development)

---

## Tech Stack

- Python (Flask)
- SQLite
- HTML, CSS, JavaScript
- Bootstrap (for UI components)

---

## Setup Guide

**1. Clone the repository**

```bash
git clone https://github.com/TahsinShan/Uniportal.git
cd Uniportal
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Initialize the database**

```bash
python init_db.py
```

**4. Run the app**

```bash
python app.py
```

Now go to `http://localhost:5000` in your browser.

---

## Project Structure

```
Uniportal/
├── app.py           # Main Flask app
├── init_db.py       # Script to initialize the database
├── database.db      # SQLite database file
├── requirements.txt # Python dependencies
├── static/          # CSS, JS, images
└── templates/       # HTML templates
```

---

## Roles & Access

- **Students**: Register, log in, enroll in courses, view updates and reports  
- **Teachers**: Log in, post class reschedules and upload course materials  
- **Admins**: Full control – add/delete courses, post events, manage access

*Admin credentials are predefined for simplicity. You can edit them in the DB or init script.*

---

## Current Limitations

- Basic validation and security (no production-level features yet)
- No user photo upload (planned)
- SMS system is minimal, works as a placeholder
- Still under development — expect updates and improvements

---

## Contributing

Open to contributions. If you have suggestions or find bugs, feel free to open an issue or submit a pull request.

---

## License

This project doesn’t currently include a license. Add one if you plan to share it publicly under specific terms.

---

## Maintainer

Built by [TahsinShan](https://github.com/TahsinShan)
