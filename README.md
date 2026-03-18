# ⚡ QuickServe – Smart Service Provider Platform
### MCA 2nd Semester Academic Project

A web-based platform to connect users with nearby home service professionals.
Built with **Python Flask**, **SQLite**, **Bootstrap 5**, and a basic **AI recommendation engine**.

---

## 📁 Project Structure

```
quickserve/
├── app.py                   ← Main Flask application (all routes + AI logic)
├── database.db              ← Auto-created SQLite database
├── requirements.txt         ← Python dependencies
│
├── templates/
│   ├── base.html            ← Base layout with navbar & footer
│   ├── index.html           ← Landing page with AI recommendation
│   ├── login.html           ← Login (User / Provider / Admin)
│   ├── register.html        ← User registration
│   ├── register_provider.html ← Provider registration
│   ├── dashboard.html       ← User dashboard
│   ├── services.html        ← Browse service providers
│   ├── provider_detail.html ← Provider profile + reviews
│   ├── booking.html         ← Book a service
│   ├── rate.html            ← Rate a completed service
│   ├── provider_dashboard.html ← Provider dashboard
│   ├── admin_dashboard.html ← Admin overview
│   ├── admin_providers.html ← Manage providers
│   ├── admin_users.html     ← Manage users
│   ├── admin_bookings.html  ← View all bookings
│   ├── admin_categories.html ← Manage categories
│   └── admin_reviews.html   ← View reviews
│
├── static/
│   ├── css/style.css        ← Custom stylesheet
│   └── js/main.js           ← Custom JavaScript
```

---

## 🚀 How to Run Locally

### Step 1 — Prerequisites
Make sure you have **Python 3.8+** installed.
```bash
python --version
```

### Step 2 — Navigate to the project folder
```bash
cd quickserve
```

### Step 3 — Create a virtual environment (recommended)
```bash
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on Mac/Linux:
source venv/bin/activate
```

### Step 4 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 5 — Run the application
```bash
python app.py
```

### Step 6 — Open in browser
```
http://127.0.0.1:5000
```

---

## 🔐 Demo Login Credentials

| Role     | Email                    | Password  |
|----------|--------------------------|-----------|
| Admin    | admin@quickserve.com     | admin123  |
| User     | rahul@example.com        | pass123   |
| User     | priya@example.com        | pass123   |
| Provider | ramesh@sp.com (Electric) | pass123   |
| Provider | suresh@sp.com (Plumber)  | pass123   |
| Provider | vikram@sp.com (AC Tech)  | pass123   |

---

## 🧩 System Roles

### 👤 User (Customer)
- Register / Login
- Browse services by category
- View provider profiles and ratings
- Book services
- Track booking status (Pending / Accepted / Completed)
- Rate and review after completion

### 🔧 Service Provider
- Register (pending admin approval)
- View incoming booking requests
- Accept, Reject, or Mark as Completed
- View customer reviews and ratings

### 🛡️ Admin
- Approve or reject service providers
- Manage service categories
- Monitor all users, bookings, and reviews

---

## 🤖 AI Feature — Smart Service Recommendation

When a user types a problem description, the system uses **NLP keyword matching** to recommend the most suitable service category.

**Examples:**
| User Types          | System Recommends  |
|---------------------|--------------------|
| "fan not working"   | Electrician        |
| "pipe leaking"      | Plumber            |
| "AC not cooling"    | AC Technician      |
| "car not starting"  | Mechanic           |
| "wall needs paint"  | Painter            |

Available on the Home page, User Dashboard, and Booking page.

---

## 🛠️ Tech Stack

| Layer    | Technology                    |
|----------|-------------------------------|
| Frontend | HTML5, CSS3, Bootstrap 5      |
| Backend  | Python Flask                  |
| Database | SQLite (via sqlite3 module)   |
| AI       | NLP Keyword Matching (custom) |
| Icons    | Font Awesome 6                |
| Fonts    | Plus Jakarta Sans, Space Mono |

---

## 📊 Database Tables

| Table              | Description                        |
|--------------------|------------------------------------|
| users              | Customer accounts                  |
| service_providers  | Provider accounts + approval status|
| categories         | Service categories                 |
| bookings           | All booking records                |
| ratings            | Customer reviews and star ratings  |

---

*QuickServe — MCA 2nd Semester Project*
