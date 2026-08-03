# 💼 JobTrack - A modern Flask-based Job Application Tracking System.

<p align="center">
  <img src="static/images/home.png" alt="JobTrack Banner" width="100%">
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple?logo=bootstrap)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Render-blue?logo=postgresql)
![Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7)

</p>

A modern **Flask-based Job Application Tracker** that helps users organize, manage, and monitor their job applications from one place.

The application includes secure authentication, resume uploads, dashboard statistics, PDF & CSV export, search/filter functionality, and is deployed on **Render** using **PostgreSQL**.

---

# 🌐 Live Demo

### https://jobtrack-flask.onrender.com/

---

# ✨ Features

## 🔐 Authentication

- User Registration
- Secure Login & Logout
- Password Hashing
- Session Management
- Protected Routes using Flask-Login

---

## 💼 Job Application Management

- Add Applications
- Edit Applications
- Delete Applications
- View All Applications
- Search by Company
- Search by Role
- Filter by Status

---

## 📊 Dashboard

- Total Applications
- Applied Jobs
- Interviews
- Offers
- Accepted Jobs
- Rejected Jobs
- Success Rate

---

## 📄 Resume Management

- Upload Resume
- Download Resume

---

## 📁 Export

- Export Applications to CSV
- Generate Professional PDF Report

---

## 🔒 Security

- Password Hashing
- User Authentication
- User-specific Data Isolation
- Environment Variables
- Protected Routes

---

# 🛠️ Tech Stack

| Category | Technologies |
|----------|--------------|
| Backend | Flask, Python |
| Database | PostgreSQL (Render), SQLAlchemy 2.0 |
| Frontend | HTML5, CSS3, Bootstrap 5, Jinja2 |
| Authentication | Flask-Login |
| Forms | Flask-WTF |
| PDF | ReportLab |
| Deployment | Render + Gunicorn |

---

# 📸 Screenshots

## 🏠 Home Page

![Home](static/images/home.png)

---

## 📊 Dashboard

![Dashboard](static/images/dashboard-preview.png)

---

## 💼 Applications

![Applications](static/images/applications.png)

---

## ➕ Add Application

![Add Application](static/images/add_application.png)

---

## 📈 Statistics

![Statistics](static/images/statistic.png)

---

# 🚀 Installation

## Clone Repository

```bash
git clone https://github.com/harshadx27/JobTrack-Flask.git

cd JobTrack-Flask
```

---

## Create Virtual Environment

```bash
python -m venv .venv
```

---

## Activate Virtual Environment

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment Variables

Create a `.env` file in the project root.

```env
SECRET_KEY=your-secret-key

DATABASE_URL=your-database-url

UPLOAD_FOLDER=static/uploads
```

---

## Run the Application

```bash
python app.py
```

Visit:

```
http://127.0.0.1:5000
```

---

# ☁️ Deployment

This application is deployed on **Render**.

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
gunicorn app:app
```

---

# 📂 Project Structure

```
JobTrack-Flask
│
├── app.py
├── forms.py
├── requirements.txt
├── Procfile
├── .env.example
│
├── static/
│   ├── css/
│   ├── images/
│   └── uploads/
│
├── templates/
│
└── instance/
```

---

# 📚 What I Learned

This project strengthened my understanding of:

- Flask Application Development
- SQLAlchemy ORM
- Database Relationships
- Authentication & Authorization
- CRUD Operations
- File Upload Handling
- CSV Export
- PDF Generation
- Dashboard Analytics
- Environment Variables
- Deployment on Render
- PostgreSQL
- Git & GitHub Workflow

---

# 🚀 Future Improvements

- Email Notifications
- Interview Reminders
- Calendar Integration
- Company Logos
- Pagination
- Sorting
- REST API
- Docker Support
- Unit Testing
- Admin Dashboard

---

# 👨‍💻 Author

**Harshad Bhadwalkar**

📧 Python Backend Developer

**GitHub**

https://github.com/harshadx27

**LinkedIn**

https://www.linkedin.com/in/harshad-bhadwalkar/

---

# ⭐ Support

If you found this project useful, consider giving it a ⭐ on GitHub.

---

# 📄 License

This project is open-source and developed for learning and portfolio purposes.
