# JobAnalyzer

JobAnalyzer is a web-based **Job Application Analyzer** built with Python, Flask, MySQL, HTML, CSS, and JavaScript.

The application helps users organize their job search, track applications, analyze job descriptions, and compare required skills with their saved skill profile.

---

## Features

### 1. User Authentication
- User registration and login
- Secure password hashing
- Remember Me option
- Session-based authentication
- Logout functionality
- User-specific application and skill data

### 2. Application Manager
Users can store and manage their job applications with details such as:
- Company
- Job title
- Location
- Job type
- Application date
- Application status
- Job description
- Notes

Applications can be:
- Added
- Viewed
- Edited
- Deleted
- Filtered through the application management interface

### 3. Dashboard Analytics
The dashboard provides an overview of the user's job search, including:
- Total applications
- Applied applications
- Interviews
- Selected applications
- Rejected applications
- Monthly application activity
- Status distribution
- Quick actions

### 4. Industry-Independent Skill Analyzer
JobAnalyzer is not restricted to software or IT jobs.

The analyzer can work with skills from areas such as:
- Software and IT
- Management and MBA
- MCA
- Banking
- Finance and Accounting
- Human Resources
- Marketing
- Sales
- Operations
- Education and Training
- Design and Creative roles
- General professional skills

Users can save their own skills and analyze a job description to identify relevant skills mentioned in the job requirements.

### 5. Profile Management
Users can:
- View their name and email
- Edit their name
- Change their email after password verification
- Change their password
- Upload a profile picture
- Manage their saved skills
- Log out from their profile

---

## How JobAnalyzer Works

The application follows a simple workflow:

```text
User
 │
 ├── Register / Login
 │
 ▼
Dashboard
 │
 ├── Manage Applications
 │     ├── Add
 │     ├── View
 │     ├── Edit
 │     └── Delete
 │
 ├── Skill Analyzer
 │     ├── Save Skills
 │     └── Analyze Job Description
 │
 └── Profile
       ├── Edit Account Details
       ├── Change Password
       ├── Profile Picture
       └── Manage Skills
```

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| MySQL | Database |
| HTML | Page structure |
| CSS | User interface and styling |
| JavaScript | Client-side interactions |
| Bootstrap Icons | Interface icons |
| python-dotenv | Environment variable management |
| mysql-connector-python | MySQL connectivity |

---

## Database Design

JobAnalyzer uses MySQL with three main tables.

### `users`

Stores account information.

```text
id
name
email
password
created_at
profile_picture
```

### `applications`

Stores each user's job applications.

```text
id
user_id
company
job_title
location
job_type
application_date
status
job_description
notes
created_at
```

The `user_id` connects an application to its owner.

### `user_skills`

Stores the skills saved by each user.

```text
id
user_id
skill
source
created_at
```

The application uses a relationship between `users`, `applications`, and `user_skills` so that users only access their own data.

---

## Project Structure

```text
JobApplicationAnalyzer/
│
├── app.py
├── .env
├── .gitignore
├── requirements.txt
│
├── templates/
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── add_application.html
│   ├── applications.html
│   ├── view_application.html
│   ├── edit_application.html
│   ├── skill_analyzer.html
│   └── profile.html
│
└── static/
    ├── css/
    ├── js/
    ├── images/
    └── uploads/
        └── profile_pictures/
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/MuhammadTahir-Shaik/JonAnalyzer
cd JobApplicationAnalyzer
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

#### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

---

## MySQL Setup

Create the database:

```sql
CREATE DATABASE job_analyzer;
USE job_analyzer;
```

Create the required tables using the project's database schema.

The application expects the database configuration to be provided through environment variables.

---

## Environment Variables

Create a `.env` file in the project root:

```text
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=YOUR_MYSQL_PASSWORD
DB_NAME=job_analyzer
SECRET_KEY=YOUR_SECRET_KEY
```

Do not commit `.env` to GitHub.

---

## Running the Application

Activate the virtual environment and run:

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

---

## Security Considerations

The application includes several basic security practices:

- Passwords are stored using password hashing rather than plain text.
- User sessions are used to protect authenticated pages.
- Database queries use parameterized values.
- Application records are queried using both application ID and logged-in user ID.
- User skills are associated with individual users.
- Sensitive configuration such as the database password is stored in `.env`.
- `.env` and the virtual environment are excluded through `.gitignore`.

---

## Skill Matching

The Skill Analyzer uses the user's saved skills and checks the job description for matching skill terms.

The matching logic uses boundary-aware regular expressions to reduce incorrect matches.

For example, a saved skill such as:

```text
Java
```

should not incorrectly match the word:

```text
JavaScript
```

This makes the basic skill matching more reliable than simple substring searching.

---

## Current Limitations

The current version focuses on manual input and rule-based skill matching.

The following features are planned improvements rather than current functionality:

- Resume file upload
- Automatic resume text extraction
- Automatic skill extraction from resumes
- More advanced NLP-based job analysis
- Job recommendation system
- Automated job-board integration
- Advanced application success-rate analytics

---

## Future Enhancements

Possible future versions can include:

1. **Resume Analyzer**
   - Upload a resume
   - Extract resume text
   - Automatically identify skills

2. **Advanced Job Description Analysis**
   - Extract technical and non-technical requirements
   - Identify experience requirements
   - Identify education requirements
   - Generate a more detailed match report

3. **Job Recommendations**
   - Recommend jobs based on the user's skill profile

4. **Advanced Analytics**
   - Application success rate
   - Interview conversion rate
   - Company-wise statistics
   - Role-wise statistics
   - Skill-gap trends

5. **Job Board Integration**
   - Connect with external job platforms through appropriate APIs

---

## Screenshots

Screenshots of the application can be added here after the final UI capture.

Recommended screenshots:

- Home page
![alt text](<Screenshot 2026-10-11 184913.png>)
- Login page
- Dashboard
- Applications page
- Application details
- Skill Analyzer
- Profile page

Example:

```text
## Dashboard

![Dashboard](screenshots/dashboard.png)
```

---

## What This Project Demonstrates

This project demonstrates practical experience with:

- Python backend development
- Flask routing
- Authentication and sessions
- CRUD operations
- MySQL database design
- SQL queries
- Relational database relationships
- Form handling
- Password hashing
- File uploads
- Data visualization
- User-specific data access
- Regular expressions
- HTML/CSS/JavaScript
- Full-stack web application development

---

## Project Goal

The goal of JobAnalyzer is to make job searching more organized and data-driven by combining **application tracking, job-description skill analysis, and job-search analytics** in one web application.

---

## Author

**Muhammad Tahir Shaik**

B.Tech Computer Science and Engineering

---

## License

This project is created for educational and portfolio purposes.
