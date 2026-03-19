"""
QuickServe – Smart Service Provider Platform
MCA 2nd Semester Academic Project
Features: OTP Login + Full Email Notification System
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3, hashlib, os, random, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "quickserve_secret_2024"
DATABASE = "database.db"

# ─────────────────────────────────────────
# AI LOCATION DETECTION (IPInfo - Free)
# ─────────────────────────────────────────

def haversine(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def get_user_coords():
    try:
        import urllib.request, json
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        if not ip or ip in ("127.0.0.1", "::1", "localhost"):
            return 28.6315, 77.2167, "Delhi"
        ip = ip.split(",")[0].strip()
        url = "https://ipinfo.io/" + ip + "/json"
        req = urllib.request.Request(url, headers={"User-Agent": "QuickServe/1.0"})
        r   = urllib.request.urlopen(req, timeout=3)
        data = json.loads(r.read())
        loc  = data.get("loc", "28.6139,77.2090").split(",")
        city = data.get("city", "Delhi")
        return float(loc[0]), float(loc[1]), city
    except:
        return 28.6139, 77.2090, "Delhi"

def get_user_city():
    try:
        import urllib.request, json
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        if not ip or ip in ("127.0.0.1", "::1", "localhost"):
            return session.get("user_city", "Delhi")
        ip = ip.split(",")[0].strip()
        url = "https://ipinfo.io/" + ip + "/json"
        req = urllib.request.Request(url, headers={"User-Agent": "QuickServe/1.0"})
        r   = urllib.request.urlopen(req, timeout=3)
        data = json.loads(r.read())
        return data.get("city", "")
    except:
        return session.get("user_city", "")

# ── EMAIL CONFIG ──
GMAIL_ADDRESS  = "quickserve41@gmail.com"
GMAIL_PASSWORD = "iavb gimy wgld tmuz"

# ─────────────────────────────────────────
# EMAIL SENDER
# ─────────────────────────────────────────
def send_email(to_email, subject, html_body):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"QuickServe <{GMAIL_ADDRESS}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ─────────────────────────────────────────
# EMAIL TEMPLATES
# ─────────────────────────────────────────
def email_base(content):
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #eee;border-radius:10px;overflow:hidden;">
      <div style="background:#1A1A2E;padding:20px;text-align:center;">
        <h1 style="color:#FF6B2C;margin:0;">⚡ QuickServe</h1>
        <p style="color:#aaa;margin:5px 0 0;">Smart Service Provider Platform</p>
      </div>
      <div style="padding:30px;background:#fff;">{content}</div>
      <div style="background:#f8f9fc;padding:15px;text-align:center;border-top:1px solid #eee;">
        <p style="color:#aaa;font-size:12px;margin:0;">Automated email from QuickServe. Do not reply.</p>
      </div>
    </div>"""

def otp_email_template(name, otp):
    return email_base(f"""
        <h2 style="color:#1A1A2E;">Hello, {name}! 👋</h2>
        <p style="color:#555;">Your One-Time Password (OTP) for QuickServe login:</p>
        <div style="background:#1A1A2E;border-radius:10px;padding:25px;text-align:center;margin:20px 0;">
          <h1 style="color:#FF6B2C;font-size:48px;letter-spacing:12px;margin:0;">{otp}</h1>
        </div>
        <p style="color:#e55a1e;font-weight:bold;">⏰ Valid for 5 minutes only.</p>
        <p style="color:#555;">If you did not request this, please ignore this email.</p>""")

def welcome_email_template(name):
    return email_base(f"""
        <h2 style="color:#1A1A2E;">Welcome to QuickServe, {name}! 🎉</h2>
        <p style="color:#555;">Your account has been successfully created. You can now:</p>
        <ul style="color:#555;">
          <li>Browse service providers by category</li>
          <li>Use AI-powered service recommendations</li>
          <li>Book and track services easily</li>
          <li>Rate and review providers</li>
        </ul>""")

def booking_request_email(provider_name, user_name, service, date, time, problem, address):
    return email_base(f"""
        <h2 style="color:#1A1A2E;">New Booking Request! 📋</h2>
        <p style="color:#555;">Hello <strong>{provider_name}</strong>, you have a new booking request.</p>
        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
          <tr style="background:#f8f9fc;"><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Customer</td><td style="padding:10px;border:1px solid #eee;">{user_name}</td></tr>
          <tr><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Service</td><td style="padding:10px;border:1px solid #eee;">{service}</td></tr>
          <tr style="background:#f8f9fc;"><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Date</td><td style="padding:10px;border:1px solid #eee;">{date}</td></tr>
          <tr><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Time</td><td style="padding:10px;border:1px solid #eee;">{time}</td></tr>
          <tr style="background:#f8f9fc;"><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Problem</td><td style="padding:10px;border:1px solid #eee;">{problem or 'Not specified'}</td></tr>
          <tr><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Address</td><td style="padding:10px;border:1px solid #eee;">{address or 'Not specified'}</td></tr>
        </table>
        <p style="color:#555;">Login to your dashboard to accept or reject this request.</p>""")

def booking_accepted_email(user_name, provider_name, provider_phone, service, date, time, address):
    return email_base(f"""
        <h2 style="color:#10B981;">Booking Accepted! ✅</h2>
        <p style="color:#555;">Hello <strong>{user_name}</strong>, your booking has been accepted!</p>
        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
          <tr style="background:#f0fdf4;"><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Provider</td><td style="padding:10px;border:1px solid #eee;">{provider_name}</td></tr>
          <tr><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Contact</td><td style="padding:10px;border:1px solid #eee;">📞 {provider_phone or 'N/A'}</td></tr>
          <tr style="background:#f0fdf4;"><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Service</td><td style="padding:10px;border:1px solid #eee;">{service}</td></tr>
          <tr><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Date & Time</td><td style="padding:10px;border:1px solid #eee;">{date} at {time}</td></tr>
          <tr style="background:#f0fdf4;"><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Address</td><td style="padding:10px;border:1px solid #eee;">{address or 'Not specified'}</td></tr>
        </table>
        <p style="color:#10B981;font-weight:bold;">The provider will arrive at the above address on the scheduled date and time.</p>""")

def booking_rejected_email(user_name, provider_name, service, date):
    return email_base(f"""
        <h2 style="color:#EF4444;">Booking Rejected ❌</h2>
        <p style="color:#555;">Hello <strong>{user_name}</strong>, your booking request was rejected.</p>
        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
          <tr style="background:#fef2f2;"><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Provider</td><td style="padding:10px;border:1px solid #eee;">{provider_name}</td></tr>
          <tr><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Service</td><td style="padding:10px;border:1px solid #eee;">{service}</td></tr>
          <tr style="background:#fef2f2;"><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Date</td><td style="padding:10px;border:1px solid #eee;">{date}</td></tr>
        </table>
        <p style="color:#555;">Don't worry! You can book another provider from our platform.</p>""")

def booking_completed_email(user_name, provider_name, service, booking_id):
    return email_base(f"""
        <h2 style="color:#1A1A2E;">Service Completed! 🏁</h2>
        <p style="color:#555;">Hello <strong>{user_name}</strong>, your service has been completed.</p>
        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
          <tr style="background:#f8f9fc;"><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Provider</td><td style="padding:10px;border:1px solid #eee;">{provider_name}</td></tr>
          <tr><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Service</td><td style="padding:10px;border:1px solid #eee;">{service}</td></tr>
        </table>
        <p style="color:#555;">Please rate your experience:</p>
        <div style="text-align:center;margin:25px 0;">
          <a href="http://127.0.0.1:5000/rate/{booking_id}" style="background:#F59E0B;color:#fff;padding:12px 30px;border-radius:8px;text-decoration:none;font-weight:bold;">⭐ Rate Now</a>
        </div>""")

def provider_approved_email(provider_name):
    return email_base(f"""
        <h2 style="color:#10B981;">Account Approved! 🎉</h2>
        <p style="color:#555;">Hello <strong>{provider_name}</strong>, your QuickServe provider account has been <strong style="color:#10B981;">approved!</strong></p>
        <p style="color:#555;">You can now login and start receiving booking requests from customers.</p>""")

def provider_rejected_email(provider_name):
    return email_base(f"""
        <h2 style="color:#EF4444;">Application Rejected ❌</h2>
        <p style="color:#555;">Hello <strong>{provider_name}</strong>, your service provider application has been rejected by the admin.</p>
        <p style="color:#555;">You may re-register with correct details or contact support.</p>""")

def booking_accepted_with_complaint_email(user_name, provider_name, provider_phone, service, date, time, address, booking_id):
    return email_base(f"""
        <h2 style="color:#10B981;">Booking Accepted! ✅</h2>
        <p style="color:#555;">Hello <strong>{user_name}</strong>, your booking has been accepted!</p>
        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
          <tr style="background:#f0fdf4;"><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Provider</td><td style="padding:10px;border:1px solid #eee;">{provider_name}</td></tr>
          <tr><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Contact</td><td style="padding:10px;border:1px solid #eee;">📞 {provider_phone or 'N/A'}</td></tr>
          <tr style="background:#f0fdf4;"><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Service</td><td style="padding:10px;border:1px solid #eee;">{service}</td></tr>
          <tr><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Date & Time</td><td style="padding:10px;border:1px solid #eee;">{date} at {time}</td></tr>
          <tr style="background:#f0fdf4;"><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Address</td><td style="padding:10px;border:1px solid #eee;">{address or 'Not specified'}</td></tr>
        </table>
        <p style="color:#10B981;font-weight:bold;">The provider will arrive at the scheduled date and time.</p>
        <hr style="border:1px solid #eee;margin:20px 0;"/>
        <p style="color:#555;font-size:13px;">⚠️ <strong>If the provider does not arrive or service quality is poor</strong>, you can file a complaint:</p>
        <div style="text-align:center;margin:15px 0;">
          <a href="http://127.0.0.1:5000/complaint/{booking_id}"
             style="background:#EF4444;color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:bold;">
            📢 File a Complaint
          </a>
        </div>""")

def complaint_warning_email(provider_name, reason, description):
    return email_base(f"""
        <h2 style="color:#F59E0B;">⚠️ Warning Notice</h2>
        <p style="color:#555;">Hello <strong>{provider_name}</strong>,</p>
        <p style="color:#555;">A complaint has been filed against you on QuickServe.</p>
        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
          <tr style="background:#fffbeb;"><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Reason</td><td style="padding:10px;border:1px solid #eee;">{reason}</td></tr>
          <tr><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Details</td><td style="padding:10px;border:1px solid #eee;">{description or 'No details provided'}</td></tr>
        </table>
        <p style="color:#F59E0B;font-weight:bold;">Please ensure better service quality. Repeated complaints may result in account suspension.</p>""")

def reschedule_request_email(user_name, provider_name, service, old_date, new_date, new_time, reason, booking_id):
    return email_base(f"""
        <h2 style="color:#3B82F6;">📅 Reschedule Request</h2>
        <p style="color:#555;">Hello <strong>{user_name}</strong>,</p>
        <p style="color:#555;"><strong>{provider_name}</strong> has requested to reschedule your booking.</p>
        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
          <tr style="background:#eff6ff;"><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Service</td><td style="padding:10px;border:1px solid #eee;">{service}</td></tr>
          <tr><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Original Date</td><td style="padding:10px;border:1px solid #eee;text-decoration:line-through;color:#aaa;">{old_date}</td></tr>
          <tr style="background:#eff6ff;"><td style="padding:10px;border:1px solid #eee;font-weight:bold;">New Date</td><td style="padding:10px;border:1px solid #eee;color:#10B981;font-weight:bold;">{new_date}</td></tr>
          <tr><td style="padding:10px;border:1px solid #eee;font-weight:bold;">New Time</td><td style="padding:10px;border:1px solid #eee;">{new_time}</td></tr>
          <tr style="background:#eff6ff;"><td style="padding:10px;border:1px solid #eee;font-weight:bold;">Reason</td><td style="padding:10px;border:1px solid #eee;">{reason or 'Not specified'}</td></tr>
        </table>
        <p style="color:#555;">Please accept or decline this reschedule request:</p>
        <div style="text-align:center;margin:20px 0;display:flex;gap:10px;justify-content:center;">
          <a href="http://127.0.0.1:5000/reschedule/respond/{booking_id}/accept"
             style="background:#10B981;color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:bold;">
            ✅ Accept
          </a>
          &nbsp;&nbsp;
          <a href="http://127.0.0.1:5000/reschedule/respond/{booking_id}/decline"
             style="background:#EF4444;color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:bold;">
            ❌ Decline & Cancel
          </a>
        </div>""")

# ─────────────────────────────────────────
# DB HELPER
# ─────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_otp():
    return str(random.randint(100000, 999999))

# ─────────────────────────────────────────
# INIT DB
# ─────────────────────────────────────────
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, phone TEXT, address TEXT, role TEXT DEFAULT 'user', created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS service_providers (provider_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, phone TEXT, category_id INTEGER, experience TEXT, address TEXT, latitude REAL DEFAULT 28.6139, longitude REAL DEFAULT 77.2090, description TEXT, is_approved INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (category_id) REFERENCES categories(category_id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS categories (category_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, icon TEXT, description TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS bookings (booking_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, provider_id INTEGER NOT NULL, service_category TEXT NOT NULL, date TEXT NOT NULL, time TEXT NOT NULL, problem TEXT, address TEXT, status TEXT DEFAULT 'Pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(user_id), FOREIGN KEY (provider_id) REFERENCES service_providers(provider_id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS ratings (rating_id INTEGER PRIMARY KEY AUTOINCREMENT, booking_id INTEGER NOT NULL, user_id INTEGER NOT NULL, provider_id INTEGER NOT NULL, stars INTEGER NOT NULL, review TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (booking_id) REFERENCES bookings(booking_id), FOREIGN KEY (user_id) REFERENCES users(user_id), FOREIGN KEY (provider_id) REFERENCES service_providers(provider_id))""")
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO categories (name, icon, description) VALUES (?,?,?)", [
            ("Electrician","⚡","Wiring, fan, switchboard repairs"),("Plumber","🔧","Pipe leaks, tap repair"),
            ("AC Technician","❄️","AC service, gas refill"),("Carpenter","🪚","Furniture repair, door work"),
            ("Mechanic","🔩","Vehicle repair, engine issues"),("Painter","🎨","Wall painting, waterproofing"),
            ("Cleaner","🧹","Home deep cleaning"),("CCTV Technician","📷","CCTV installation and repair")])
        conn.commit()
    cur.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO users (name, email, password, phone, role) VALUES (?,?,?,?,'admin')", ("Admin","admin@quickserve.com",hash_password("admin123"),"9999999999"))
        conn.commit()
    cur.execute("SELECT COUNT(*) FROM users WHERE role='user'")
    if cur.fetchone()[0] == 0:
        for u in [("Rahul Sharma","rahul@example.com",hash_password("pass123"),"9876543210","Delhi"),("Priya Singh","priya@example.com",hash_password("pass123"),"9876543211","Mumbai"),("Amit Kumar","amit@example.com",hash_password("pass123"),"9876543212","Bangalore")]:
            cur.execute("INSERT INTO users (name, email, password, phone, address) VALUES (?,?,?,?,?)", u)
        conn.commit()
    cur.execute("SELECT COUNT(*) FROM service_providers")
    if cur.fetchone()[0] == 0:
        # Providers with specific Delhi areas and lat/lng coordinates
        providers = [
            # Electricians (category_id=1)
            ("Priyanshu Sharma", "priyanshu@sp.com", hash_password("pass123"), "9811111101", 1, "5 years", "Rohini, Delhi",        28.7041, 77.1025, "Expert in home wiring, fan fitting and switchboard repair.", 1),
            ("Mayank Verma",     "mayank@sp.com",     hash_password("pass123"), "9811111102", 1, "3 years", "Dwarka, Delhi",        28.5921, 77.0460, "Specializes in short circuit fixing and MCB panel work.",    1),
            # Plumbers (category_id=2)
            ("Yogesh Kumar",     "yogesh@sp.com",     hash_password("pass123"), "9811111103", 2, "6 years", "Karol Bagh, Delhi",    28.6514, 77.1907, "Expert in pipe leakage, tap repair and geyser installation.", 1),
            ("Prakash Singh",    "prakash@sp.com",    hash_password("pass123"), "9811111104", 2, "4 years", "Lajpat Nagar, Delhi",  28.5677, 77.2436, "Specialist in bathroom fitting and drain blockage removal.",  1),
            # AC Technicians (category_id=3)
            ("Vinod Yadav",      "vinod@sp.com",      hash_password("pass123"), "9811111105", 3, "7 years", "Janakpuri, Delhi",     28.6219, 77.0878, "AC gas refilling, servicing and cooling problem expert.",     1),
            ("Raamu Prasad",     "raamu@sp.com",      hash_password("pass123"), "9811111106", 3, "5 years", "Pitampura, Delhi",     28.7012, 77.1305, "All AC brands servicing, split and window AC repair.",        1),
            # Carpenters (category_id=4)
            ("Ballu Mistri",     "ballu@sp.com",      hash_password("pass123"), "9811111107", 4, "10 years","Saket, Delhi",         28.5244, 77.2066, "Furniture repair, door-window fitting and almirah work.",     1),
            ("Ajay Carpenter",   "ajay@sp.com",       hash_password("pass123"), "9811111108", 4, "6 years", "Mayur Vihar, Delhi",   28.6080, 77.2920, "Custom furniture making and wooden door installation.",       1),
            # Mechanics (category_id=5)
            ("Sodi Mechanic",    "sodi@sp.com",       hash_password("pass123"), "9811111109", 5, "8 years", "Shahdara, Delhi",      28.6731, 77.2887, "Car and bike engine repair, tyre and brake specialist.",      1),
            ("Gogi Motors",      "gogi@sp.com",       hash_password("pass123"), "9811111110", 5, "5 years", "Uttam Nagar, Delhi",   28.6215, 77.0540, "All vehicle servicing, battery and oil change expert.",       1),
            # Painters (category_id=6)
            ("Bablu Painter",    "bablu@sp.com",      hash_password("pass123"), "9811111111", 6, "7 years", "Vasant Kunj, Delhi",   28.5200, 77.1577, "Interior and exterior wall painting, waterproofing expert.",  1),
            ("Chandu Colors",    "chandu@sp.com",     hash_password("pass123"), "9811111112", 6, "4 years", "Preet Vihar, Delhi",   28.6447, 77.2945, "Asian paints specialist, texture and design painting.",       1),
            # Cleaners (category_id=7)
            ("Vinayak Cleaning", "vinayak@sp.com",    hash_password("pass123"), "9811111113", 7, "3 years", "Greater Kailash, Delhi",28.5494,77.2362, "Home deep cleaning, sofa and carpet cleaning expert.",        1),
            ("Naman Services",   "naman@sp.com",      hash_password("pass123"), "9811111114", 7, "2 years", "Vikaspuri, Delhi",     28.6388, 77.0708, "Office and residential cleaning with eco-friendly products.", 1),
            # CCTV Technicians (category_id=8)
            ("Iqbal Security",   "iqbal@sp.com",      hash_password("pass123"), "9811111115", 8, "6 years", "Malviya Nagar, Delhi", 28.5274, 77.2073, "CCTV installation, DVR setup and network camera expert.",     1),
            ("Shahrukh Tech",    "shahrukh@sp.com",   hash_password("pass123"), "9811111116", 8, "4 years", "Shalimar Bagh, Delhi", 28.7148, 77.1583, "All brands CCTV repair and security system installation.",    1),
        ]
        for p in providers:
            cur.execute("INSERT INTO service_providers (name,email,password,phone,category_id,experience,address,latitude,longitude,description,is_approved) VALUES (?,?,?,?,?,?,?,?,?,?,?)", p)
        conn.commit()
    cur.execute("SELECT COUNT(*) FROM bookings")
    if cur.fetchone()[0] == 0:
        for b in [(1,1,"Electrician","2024-07-10","10:00","Fan not working","Delhi","Completed"),(2,2,"Plumber","2024-07-11","11:00","Pipe leakage","Mumbai","Accepted"),(3,3,"AC Technician","2024-07-12","14:00","AC not cooling","Bangalore","Pending")]:
            cur.execute("INSERT INTO bookings (user_id, provider_id, service_category, date, time, problem, address, status) VALUES (?,?,?,?,?,?,?,?)", b)
        conn.commit()
    # Complaints table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id    INTEGER NOT NULL,
            user_id       INTEGER NOT NULL,
            provider_id   INTEGER NOT NULL,
            reason        TEXT NOT NULL,
            description   TEXT,
            status        TEXT DEFAULT 'Pending',
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id)  REFERENCES bookings(booking_id),
            FOREIGN KEY (user_id)     REFERENCES users(user_id),
            FOREIGN KEY (provider_id) REFERENCES service_providers(provider_id)
        )
    """)

    # Reschedule requests table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reschedules (
            reschedule_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id     INTEGER NOT NULL,
            provider_id    INTEGER NOT NULL,
            new_date       TEXT NOT NULL,
            new_time       TEXT NOT NULL,
            reason         TEXT,
            status         TEXT DEFAULT 'Pending',
            created_at     TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id)  REFERENCES bookings(booking_id),
            FOREIGN KEY (provider_id) REFERENCES service_providers(provider_id)
        )
    """)
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM ratings")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO ratings (booking_id, user_id, provider_id, stars, review) VALUES (1,1,1,5,'Excellent work!')")
        conn.commit()
    conn.close()

# ─────────────────────────────────────────
# AI NLP
# ─────────────────────────────────────────
SERVICE_KEYWORDS = {
    "Electrician":["fan","light","bulb","switch","wire","wiring","electric","socket","plug","fuse","short circuit","power","current"],
    "Plumber":["pipe","water","leak","tap","drain","flush","toilet","bathroom","sink","geyser","tank","blockage"],
    "AC Technician":["ac","air conditioner","cooling","refrigerator","fridge","freeze","cool","temperature","gas","compressor"],
    "Carpenter":["door","window","furniture","wood","cabinet","shelf","almirah","table","chair","hinge"],
    "Mechanic":["car","bike","vehicle","engine","tyre","brake","battery","oil","gear","clutch"],
    "Painter":["paint","wall","colour","color","damp","stain","peeling"],
    "Cleaner":["clean","dust","dirty","mess","sweep","mop","wash"],
    "CCTV Technician":["cctv","camera","surveillance","dvr","recording","security"],
}

def recommend_service(problem_text):
    text = problem_text.lower()
    recs = []
    for service, keywords in SERVICE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                if service not in recs: recs.append(service)
                break
    return recs if recs else ["General Service"]

def login_required(role=None):
    if "user_id" not in session: return False
    if role and session.get("role") != role: return False
    return True

# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────
@app.route("/")
def index():
    conn = get_db()
    categories     = conn.execute("SELECT * FROM categories").fetchall()
    total_providers= conn.execute("SELECT COUNT(*) FROM service_providers WHERE is_approved=1").fetchone()[0]
    total_users    = conn.execute("SELECT COUNT(*) FROM users WHERE role='user'").fetchone()[0]
    total_bookings = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    conn.close()
    # Detect user city via IP
    detected_city = get_user_city()
    if detected_city:
        session["detected_city"] = detected_city
    return render_template("index.html", categories=categories,
                           total_providers=total_providers,
                           total_users=total_users,
                           total_bookings=total_bookings,
                           detected_city=detected_city)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email    = request.form["email"]
        password = hash_password(request.form["password"])
        role     = request.form["role"]
        conn     = get_db()
        user     = None
        if role in ("admin","user"):
            user = conn.execute("SELECT * FROM users WHERE email=? AND password=? AND role=?", (email,password,role)).fetchone()
        elif role == "provider":
            user = conn.execute("SELECT * FROM service_providers WHERE email=? AND password=?", (email,password)).fetchone()
            if user and user["is_approved"] != 1:
                flash("Your account is pending admin approval.", "warning")
                conn.close()
                return redirect(url_for("login"))
        conn.close()
        if user:
            # OTP only for regular users — Admin & Provider login directly
            if role == "user":
                otp = generate_otp()
                session["otp"]           = otp
                session["otp_email"]     = email
                session["otp_role"]      = role
                session["otp_user_id"]   = user["user_id"]
                session["otp_user_name"] = user["name"]
                session["otp_expiry"]    = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
                send_email(email, "QuickServe – Your OTP Code 🔐", otp_email_template(user["name"], otp))
                flash(f"OTP sent to {email}. Check your inbox!", "info")
                return redirect(url_for("verify_otp"))
            else:
                # Admin and Provider — direct login (no OTP)
                session["user_id"] = user["user_id"] if role == "admin" else user["provider_id"]
                session["name"]    = user["name"]
                session["role"]    = role
                if role == "admin":    return redirect(url_for("admin_dashboard"))
                elif role == "provider": return redirect(url_for("provider_dashboard"))
        flash("Invalid credentials. Please try again.", "danger")
    return render_template("login.html")

@app.route("/verify-otp", methods=["GET","POST"])
def verify_otp():
    if "otp" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        entered = request.form.get("otp","").strip()
        action  = request.form.get("action","verify")
        if action == "resend":
            otp = generate_otp()
            session["otp"]        = otp
            session["otp_expiry"] = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
            send_email(session["otp_email"], "QuickServe – New OTP 🔐", otp_email_template(session["otp_user_name"], otp))
            flash("New OTP sent to your email!", "info")
            return redirect(url_for("verify_otp"))
        expiry = datetime.strptime(session["otp_expiry"], "%Y-%m-%d %H:%M:%S")
        if datetime.now() > expiry:
            for k in ["otp","otp_email","otp_role","otp_user_id","otp_user_name","otp_expiry"]: session.pop(k,None)
            flash("OTP expired! Please login again.", "danger")
            return redirect(url_for("login"))
        if entered == session["otp"]:
            session["user_id"] = session["otp_user_id"]
            session["name"]    = session["otp_user_name"]
            session["role"]    = session["otp_role"]
            for k in ["otp","otp_email","otp_role","otp_user_id","otp_user_name","otp_expiry"]: session.pop(k,None)
            if session["role"] == "admin":    return redirect(url_for("admin_dashboard"))
            elif session["role"] == "provider": return redirect(url_for("provider_dashboard"))
            else:                              return redirect(url_for("dashboard"))
        flash("Invalid OTP! Please try again.", "danger")
    return render_template("verify_otp.html", email=session.get("otp_email",""))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name     = request.form["name"]
        email    = request.form["email"]
        password = request.form["password"]
        phone    = request.form.get("phone","")
        address  = request.form.get("address","")

        # Check if email already registered
        conn = get_db()
        existing = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        if existing:
            flash("Email already registered. Please login.", "danger")
            return redirect(url_for("register"))

        # Store registration data in session and send OTP
        otp = generate_otp()
        session["reg_otp"]      = otp
        session["reg_email"]    = email
        session["reg_name"]     = name
        session["reg_password"] = hash_password(password)
        session["reg_phone"]    = phone
        session["reg_address"]  = address
        session["reg_expiry"]   = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")

        send_email(email, "QuickServe – Verify Your Email 🔐", otp_email_template(name, otp))
        flash(f"OTP sent to {email}. Please verify to complete registration!", "info")
        return redirect(url_for("verify_register_otp"))

    return render_template("register.html")

@app.route("/verify-register-otp", methods=["GET","POST"])
def verify_register_otp():
    if "reg_otp" not in session:
        return redirect(url_for("register"))

    if request.method == "POST":
        entered = request.form.get("otp","").strip()
        action  = request.form.get("action","verify")

        # Resend OTP
        if action == "resend":
            otp = generate_otp()
            session["reg_otp"]    = otp
            session["reg_expiry"] = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
            send_email(session["reg_email"], "QuickServe – New OTP 🔐", otp_email_template(session["reg_name"], otp))
            flash("New OTP sent to your email!", "info")
            return redirect(url_for("verify_register_otp"))

        # Check expiry
        expiry = datetime.strptime(session["reg_expiry"], "%Y-%m-%d %H:%M:%S")
        if datetime.now() > expiry:
            for k in ["reg_otp","reg_email","reg_name","reg_password","reg_phone","reg_address","reg_expiry"]:
                session.pop(k, None)
            flash("OTP expired! Please register again.", "danger")
            return redirect(url_for("register"))

        # Verify OTP
        if entered == session["reg_otp"]:
            try:
                conn = get_db()
                conn.execute(
                    "INSERT INTO users (name,email,password,phone,address) VALUES (?,?,?,?,?)",
                    (session["reg_name"], session["reg_email"], session["reg_password"],
                     session["reg_phone"], session["reg_address"])
                )
                conn.commit()
                conn.close()
                # Send welcome email
                send_email(session["reg_email"], "Welcome to QuickServe! 🎉", welcome_email_template(session["reg_name"]))
                # Clear reg session
                for k in ["reg_otp","reg_email","reg_name","reg_password","reg_phone","reg_address","reg_expiry"]:
                    session.pop(k, None)
                flash("Email verified! Registration successful. Please login.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("Email already registered.", "danger")
                return redirect(url_for("register"))
        else:
            flash("Invalid OTP! Please try again.", "danger")

    return render_template("verify_otp.html",
                           email=session.get("reg_email",""),
                           purpose="register")

@app.route("/register-provider", methods=["GET","POST"])
def register_provider():
    conn=get_db(); categories=conn.execute("SELECT * FROM categories").fetchall()
    if request.method == "POST":
        name=request.form["name"]; email=request.form["email"]; password=hash_password(request.form["password"])
        phone=request.form.get("phone",""); category_id=request.form.get("category_id"); experience=request.form.get("experience","")
        address=request.form.get("address",""); description=request.form.get("description","")
        try:
            conn.execute("INSERT INTO service_providers (name,email,password,phone,category_id,experience,address,description) VALUES (?,?,?,?,?,?,?,?)",(name,email,password,phone,category_id,experience,address,description))
            conn.commit(); conn.close()
            flash("Registration submitted! Await admin approval.","info")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError: flash("Email already registered.","danger")
    conn.close()
    return render_template("register_provider.html", categories=categories)

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    if not login_required("user"): return redirect(url_for("login"))
    conn=get_db()
    bookings=conn.execute("SELECT b.*, sp.name as provider_name, sp.phone as provider_phone FROM bookings b JOIN service_providers sp ON b.provider_id=sp.provider_id WHERE b.user_id=? ORDER BY b.created_at DESC",(session["user_id"],)).fetchall()
    categories=conn.execute("SELECT * FROM categories").fetchall(); conn.close()
    return render_template("dashboard.html", bookings=bookings, categories=categories)

@app.route("/services")
def services():
    if not login_required("user"): return redirect(url_for("login"))
    conn = get_db()
    category_filter = request.args.get("category", "")
    # Check if real GPS coords passed from browser
    gps_lat = request.args.get("lat")
    gps_lon = request.args.get("lon")

    if gps_lat and gps_lon:
        # Real GPS from browser
        user_lat  = float(gps_lat)
        user_lon  = float(gps_lon)
        user_city = session.get("detected_city", "Your Location")
    else:
        # Fallback to IP detection
        user_lat, user_lon, user_city = get_user_coords()
        session["detected_city"] = user_city

    q = "SELECT sp.*, c.name as cat_name, COALESCE(AVG(r.stars),0) as avg_rating, COUNT(r.rating_id) as review_count, COALESCE(sp.latitude,28.6139) as lat, COALESCE(sp.longitude,77.2090) as lon FROM service_providers sp JOIN categories c ON sp.category_id=c.category_id LEFT JOIN ratings r ON sp.provider_id=r.provider_id WHERE sp.is_approved=1"
    all_p = conn.execute(q + " AND c.name=? GROUP BY sp.provider_id", (category_filter,)).fetchall() if category_filter else conn.execute(q + " GROUP BY sp.provider_id").fetchall()

    # Calculate distance and sort
    providers_with_dist = sorted(
        [(round(haversine(user_lat, user_lon, p["lat"], p["lon"]), 1), p) for p in all_p],
        key=lambda x: x[0]
    )

    nearby_providers = [(d,p) for d,p in providers_with_dist if d <= 10]
    other_providers  = [(d,p) for d,p in providers_with_dist if d > 10]

    categories = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()
    return render_template("services.html",
                           nearby_providers=nearby_providers,
                           other_providers=other_providers,
                           categories=categories,
                           selected=category_filter,
                           user_city=user_city,
                           detected_city=user_city,
                           user_lat=user_lat,
                           user_lon=user_lon)

@app.route("/provider/<int:provider_id>")
def provider_detail(provider_id):
    if not login_required("user"): return redirect(url_for("login"))
    conn=get_db()
    provider=conn.execute("SELECT sp.*, c.name as cat_name FROM service_providers sp JOIN categories c ON sp.category_id=c.category_id WHERE sp.provider_id=? AND sp.is_approved=1",(provider_id,)).fetchone()
    reviews=conn.execute("SELECT r.*, u.name as user_name FROM ratings r JOIN users u ON r.user_id=u.user_id WHERE r.provider_id=? ORDER BY r.created_at DESC",(provider_id,)).fetchall()
    avg_rating=conn.execute("SELECT COALESCE(AVG(stars),0) FROM ratings WHERE provider_id=?",(provider_id,)).fetchone()[0]; conn.close()
    if not provider: flash("Provider not found.","danger"); return redirect(url_for("services"))
    return render_template("provider_detail.html", provider=provider, reviews=reviews, avg_rating=round(avg_rating,1))

@app.route("/book/<int:provider_id>", methods=["GET","POST"])
def book_service(provider_id):
    if not login_required("user"): return redirect(url_for("login"))
    conn=get_db()
    provider=conn.execute("SELECT sp.*, c.name as cat_name FROM service_providers sp JOIN categories c ON sp.category_id=c.category_id WHERE sp.provider_id=?",(provider_id,)).fetchone()
    if request.method == "POST":
        date=request.form["date"]; time=request.form["time"]; problem=request.form.get("problem",""); address=request.form.get("address","")
        conn.execute("INSERT INTO bookings (user_id,provider_id,service_category,date,time,problem,address) VALUES (?,?,?,?,?,?,?)",(session["user_id"],provider_id,provider["cat_name"],date,time,problem,address))
        conn.commit()
        send_email(provider["email"],"QuickServe – New Booking Request 📋",booking_request_email(provider["name"],session["name"],provider["cat_name"],date,time,problem,address))
        conn.close()
        flash("Booking sent! Provider notified via email. ✅","success")
        return redirect(url_for("dashboard"))
    conn.close()
    from datetime import date as dt; today=dt.today().strftime("%Y-%m-%d")
    return render_template("booking.html", provider=provider, today=today)

@app.route("/rate/<int:booking_id>", methods=["GET","POST"])
def rate_booking(booking_id):
    if not login_required("user"): return redirect(url_for("login"))
    conn=get_db()
    booking=conn.execute("SELECT * FROM bookings WHERE booking_id=? AND user_id=?",(booking_id,session["user_id"])).fetchone()
    if not booking or booking["status"]!="Completed": flash("Cannot rate this booking.","warning"); return redirect(url_for("dashboard"))
    existing=conn.execute("SELECT * FROM ratings WHERE booking_id=?",(booking_id,)).fetchone()
    if existing: flash("Already rated.","info"); return redirect(url_for("dashboard"))
    if request.method=="POST":
        stars=int(request.form["stars"]); review=request.form.get("review","")
        conn.execute("INSERT INTO ratings (booking_id,user_id,provider_id,stars,review) VALUES (?,?,?,?,?)",(booking_id,session["user_id"],booking["provider_id"],stars,review))
        conn.commit(); conn.close()
        flash("Thank you for your review! ⭐","success")
        return redirect(url_for("dashboard"))
    conn.close()
    return render_template("rate.html", booking=booking)

@app.route("/recommend", methods=["POST"])
def recommend():
    data        = request.get_json()
    problem     = data.get("problem", "")
    services    = recommend_service(problem)
    user_city   = session.get("detected_city", "") or session.get("user_city", "")

    # Count nearby providers for recommended services
    conn = get_db()
    nearby_info = []
    for svc in services:
        if user_city:
            count = conn.execute(
                "SELECT COUNT(*) FROM service_providers sp JOIN categories c ON sp.category_id=c.category_id WHERE sp.is_approved=1 AND c.name=? AND sp.address LIKE ?",
                (svc, f"%{user_city}%")
            ).fetchone()[0]
            nearby_info.append({"service": svc, "count": count, "city": user_city})
        else:
            nearby_info.append({"service": svc, "count": 0, "city": ""})
    conn.close()

    return jsonify({
        "recommendations": services,
        "nearby":          nearby_info,
        "city":            user_city
    })

@app.route("/provider/dashboard")
def provider_dashboard():
    if not login_required("provider"): return redirect(url_for("login"))
    pid=session["user_id"]; conn=get_db()
    bookings=conn.execute("SELECT b.*, u.name as user_name, u.phone as user_phone FROM bookings b JOIN users u ON b.user_id=u.user_id WHERE b.provider_id=? ORDER BY b.created_at DESC",(pid,)).fetchall()
    reviews=conn.execute("SELECT r.*, u.name as user_name FROM ratings r JOIN users u ON r.user_id=u.user_id WHERE r.provider_id=? ORDER BY r.created_at DESC",(pid,)).fetchall()
    avg_rating=conn.execute("SELECT COALESCE(AVG(stars),0) FROM ratings WHERE provider_id=?",(pid,)).fetchone()[0]
    stats={"pending":conn.execute("SELECT COUNT(*) FROM bookings WHERE provider_id=? AND status='Pending'",(pid,)).fetchone()[0],"accepted":conn.execute("SELECT COUNT(*) FROM bookings WHERE provider_id=? AND status='Accepted'",(pid,)).fetchone()[0],"completed":conn.execute("SELECT COUNT(*) FROM bookings WHERE provider_id=? AND status='Completed'",(pid,)).fetchone()[0]}
    conn.close()
    return render_template("provider_dashboard.html", bookings=bookings, reviews=reviews, avg_rating=round(avg_rating,1), stats=stats)

@app.route("/provider/update-booking/<int:booking_id>/<action>")
def update_booking(booking_id, action):
    if not login_required("provider"): return redirect(url_for("login"))
    status_map={"accept":"Accepted","reject":"Rejected","complete":"Completed"}
    new_status=status_map.get(action)
    if new_status:
        conn=get_db()
        conn.execute("UPDATE bookings SET status=? WHERE booking_id=? AND provider_id=?",(new_status,booking_id,session["user_id"]))
        conn.commit()
        booking=conn.execute("SELECT b.*, u.name as user_name, u.email as user_email, sp.name as provider_name, sp.phone as provider_phone FROM bookings b JOIN users u ON b.user_id=u.user_id JOIN service_providers sp ON b.provider_id=sp.provider_id WHERE b.booking_id=?",(booking_id,)).fetchone()
        conn.close()
        if booking:
            if new_status=="Accepted":
                send_email(booking["user_email"],"QuickServe – Booking Accepted! ✅",
                    booking_accepted_with_complaint_email(
                        booking["user_name"],booking["provider_name"],booking["provider_phone"],
                        booking["service_category"],booking["date"],booking["time"],
                        booking["address"],booking_id))
            elif new_status=="Rejected":
                send_email(booking["user_email"],"QuickServe – Booking Rejected ❌",booking_rejected_email(booking["user_name"],booking["provider_name"],booking["service_category"],booking["date"]))
            elif new_status=="Completed":
                send_email(booking["user_email"],"QuickServe – Service Completed! ⭐ Rate Now",booking_completed_email(booking["user_name"],booking["provider_name"],booking["service_category"],booking_id))
        flash(f"Booking {new_status}! User notified via email. ✅","success")
    return redirect(url_for("provider_dashboard"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if not login_required("admin"): return redirect(url_for("login"))
    conn=get_db()
    stats={"users":conn.execute("SELECT COUNT(*) FROM users WHERE role='user'").fetchone()[0],"providers":conn.execute("SELECT COUNT(*) FROM service_providers WHERE is_approved=1").fetchone()[0],"pending":conn.execute("SELECT COUNT(*) FROM service_providers WHERE is_approved=0").fetchone()[0],"bookings":conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]}
    pending_providers=conn.execute("SELECT sp.*, c.name as cat_name FROM service_providers sp JOIN categories c ON sp.category_id=c.category_id WHERE sp.is_approved=0").fetchall()
    recent_bookings=conn.execute("SELECT b.*, u.name as user_name, sp.name as provider_name FROM bookings b JOIN users u ON b.user_id=u.user_id JOIN service_providers sp ON b.provider_id=sp.provider_id ORDER BY b.created_at DESC LIMIT 10").fetchall()
    conn.close()
    return render_template("admin_dashboard.html", stats=stats, pending_providers=pending_providers, recent_bookings=recent_bookings)

@app.route("/admin/providers")
def admin_providers():
    if not login_required("admin"): return redirect(url_for("login"))
    conn=get_db()
    providers=conn.execute("SELECT sp.*, c.name as cat_name, COALESCE(AVG(r.stars),0) as avg_rating FROM service_providers sp JOIN categories c ON sp.category_id=c.category_id LEFT JOIN ratings r ON sp.provider_id=r.provider_id GROUP BY sp.provider_id ORDER BY sp.created_at DESC").fetchall()
    conn.close()
    return render_template("admin_providers.html", providers=providers)

@app.route("/admin/approve/<int:provider_id>/<int:status>")
def approve_provider(provider_id, status):
    if not login_required("admin"): return redirect(url_for("login"))
    conn=get_db()
    provider=conn.execute("SELECT * FROM service_providers WHERE provider_id=?",(provider_id,)).fetchone()
    conn.execute("UPDATE service_providers SET is_approved=? WHERE provider_id=?",(status,provider_id)); conn.commit(); conn.close()
    if provider:
        if status==1: send_email(provider["email"],"QuickServe – Account Approved! 🎉",provider_approved_email(provider["name"]))
        else:         send_email(provider["email"],"QuickServe – Application Status",provider_rejected_email(provider["name"]))
    flash(f"Provider {'approved' if status==1 else 'rejected'} and notified via email!","success")
    return redirect(url_for("admin_providers"))

@app.route("/admin/users")
def admin_users():
    if not login_required("admin"): return redirect(url_for("login"))
    conn=get_db(); users=conn.execute("SELECT * FROM users WHERE role='user' ORDER BY created_at DESC").fetchall(); conn.close()
    return render_template("admin_users.html", users=users)

@app.route("/admin/bookings")
def admin_bookings():
    if not login_required("admin"): return redirect(url_for("login"))
    conn=get_db(); bookings=conn.execute("SELECT b.*, u.name as user_name, sp.name as provider_name FROM bookings b JOIN users u ON b.user_id=u.user_id JOIN service_providers sp ON b.provider_id=sp.provider_id ORDER BY b.created_at DESC").fetchall(); conn.close()
    return render_template("admin_bookings.html", bookings=bookings)

@app.route("/admin/categories", methods=["GET","POST"])
def admin_categories():
    if not login_required("admin"): return redirect(url_for("login"))
    conn=get_db()
    if request.method=="POST":
        conn.execute("INSERT INTO categories (name,icon,description) VALUES (?,?,?)",(request.form["name"],request.form.get("icon","🔧"),request.form.get("description",""))); conn.commit(); flash("Category added.","success")
    categories=conn.execute("SELECT * FROM categories").fetchall(); conn.close()
    return render_template("admin_categories.html", categories=categories)

@app.route("/admin/delete-category/<int:cat_id>")
def delete_category(cat_id):
    if not login_required("admin"): return redirect(url_for("login"))
    conn=get_db(); conn.execute("DELETE FROM categories WHERE category_id=?",(cat_id,)); conn.commit(); conn.close()
    flash("Category deleted.","info"); return redirect(url_for("admin_categories"))

@app.route("/admin/reviews")
def admin_reviews():
    if not login_required("admin"): return redirect(url_for("login"))
    conn=get_db(); reviews=conn.execute("SELECT r.*, u.name as user_name, sp.name as provider_name FROM ratings r JOIN users u ON r.user_id=u.user_id JOIN service_providers sp ON r.provider_id=sp.provider_id ORDER BY r.created_at DESC").fetchall(); conn.close()
    return render_template("admin_reviews.html", reviews=reviews)

# ─────────────────────────────────────────
# COMPLAINT ROUTES
# ─────────────────────────────────────────

@app.route("/complaint/<int:booking_id>", methods=["GET","POST"])
def file_complaint(booking_id):
    if not login_required("user"): return redirect(url_for("login"))
    conn = get_db()
    booking = conn.execute(
        "SELECT b.*, sp.name as provider_name FROM bookings b JOIN service_providers sp ON b.provider_id=sp.provider_id WHERE b.booking_id=? AND b.user_id=?",
        (booking_id, session["user_id"])).fetchone()
    if not booking:
        flash("Booking not found.", "danger"); return redirect(url_for("dashboard"))
    existing = conn.execute("SELECT * FROM complaints WHERE booking_id=? AND user_id=?",
                            (booking_id, session["user_id"])).fetchone()
    if existing:
        flash("Complaint already filed for this booking.", "info"); conn.close(); return redirect(url_for("dashboard"))
    if request.method == "POST":
        reason=request.form.get("reason",""); description=request.form.get("description","")
        conn.execute("INSERT INTO complaints (booking_id,user_id,provider_id,reason,description) VALUES (?,?,?,?,?)",
                     (booking_id, session["user_id"], booking["provider_id"], reason, description))
        conn.commit()
        send_email(GMAIL_ADDRESS, "QuickServe – New Complaint 📢",
            email_base(f"<h3>New Complaint Filed</h3><p><b>User:</b> {session['name']}<br><b>Provider:</b> {booking['provider_name']}<br><b>Reason:</b> {reason}<br><b>Details:</b> {description or 'N/A'}</p>"))
        conn.close()
        flash("Complaint filed! Admin has been notified. ✅", "success")
        return redirect(url_for("dashboard"))
    conn.close()
    return render_template("complaint.html", booking=booking)

# ─────────────────────────────────────────
# RESCHEDULE ROUTES
# ─────────────────────────────────────────

@app.route("/provider/reschedule/<int:booking_id>", methods=["GET","POST"])
def propose_reschedule(booking_id):
    if not login_required("provider"): return redirect(url_for("login"))
    conn = get_db()
    booking = conn.execute(
        "SELECT b.*, u.name as user_name, u.email as user_email FROM bookings b JOIN users u ON b.user_id=u.user_id WHERE b.booking_id=? AND b.provider_id=?",
        (booking_id, session["user_id"])).fetchone()
    if not booking:
        flash("Booking not found.", "danger"); return redirect(url_for("provider_dashboard"))
    if request.method == "POST":
        new_date=request.form.get("new_date",""); new_time=request.form.get("new_time",""); reason=request.form.get("reason","")
        conn.execute("INSERT INTO reschedules (booking_id,provider_id,new_date,new_time,reason) VALUES (?,?,?,?,?)",
                     (booking_id, session["user_id"], new_date, new_time, reason))
        conn.execute("UPDATE bookings SET status='Reschedule Pending' WHERE booking_id=?", (booking_id,))
        conn.commit()
        send_email(booking["user_email"], "QuickServe – Reschedule Request 📅",
            reschedule_request_email(booking["user_name"], session["name"],
                booking["service_category"], booking["date"], new_date, new_time, reason, booking_id))
        conn.close()
        flash("Reschedule request sent to user! ✅", "success")
        return redirect(url_for("provider_dashboard"))
    conn.close()
    from datetime import date as dt; today=dt.today().strftime("%Y-%m-%d")
    return render_template("reschedule.html", booking=booking, today=today)

@app.route("/reschedule/respond/<int:booking_id>/<action>")
def respond_reschedule(booking_id, action):
    if not login_required("user"): return redirect(url_for("login"))
    conn = get_db()
    reschedule = conn.execute(
        "SELECT * FROM reschedules WHERE booking_id=? AND status='Pending' ORDER BY created_at DESC LIMIT 1",
        (booking_id,)).fetchone()
    if not reschedule:
        flash("No pending reschedule found.", "warning"); return redirect(url_for("dashboard"))
    if action == "accept":
        conn.execute("UPDATE bookings SET date=?, time=?, status='Accepted' WHERE booking_id=?",
                     (reschedule["new_date"], reschedule["new_time"], booking_id))
        conn.execute("UPDATE reschedules SET status='Accepted' WHERE reschedule_id=?", (reschedule["reschedule_id"],))
        conn.commit(); conn.close()
        flash(f"Reschedule accepted! New date: {reschedule['new_date']} at {reschedule['new_time']} ✅", "success")
    elif action == "decline":
        conn.execute("UPDATE bookings SET status='Cancelled' WHERE booking_id=?", (booking_id,))
        conn.execute("UPDATE reschedules SET status='Declined' WHERE reschedule_id=?", (reschedule["reschedule_id"],))
        conn.commit(); conn.close()
        flash("Reschedule declined. Booking cancelled.", "info")
    return redirect(url_for("dashboard"))

@app.route("/admin/complaints")
def admin_complaints():
    if not login_required("admin"): return redirect(url_for("login"))
    conn = get_db()
    complaints = conn.execute("""
        SELECT c.*, u.name as user_name, sp.name as provider_name, sp.email as provider_email,
               b.service_category, b.date
        FROM complaints c
        JOIN users u ON c.user_id=u.user_id
        JOIN service_providers sp ON c.provider_id=sp.provider_id
        JOIN bookings b ON c.booking_id=b.booking_id
        ORDER BY c.created_at DESC
    """).fetchall()
    conn.close()
    return render_template("admin_complaints.html", complaints=complaints)

@app.route("/admin/complaint-action/<int:complaint_id>/<action>")
def complaint_action(complaint_id, action):
    if not login_required("admin"): return redirect(url_for("login"))
    conn = get_db()
    complaint = conn.execute(
        "SELECT c.*, sp.name as provider_name, sp.email as provider_email FROM complaints c JOIN service_providers sp ON c.provider_id=sp.provider_id WHERE c.complaint_id=?",
        (complaint_id,)).fetchone()
    if complaint:
        if action == "warn":
            conn.execute("UPDATE complaints SET status='Warning Issued' WHERE complaint_id=?", (complaint_id,))
            send_email(complaint["provider_email"], "QuickServe – Warning Notice ⚠️",
                complaint_warning_email(complaint["provider_name"], complaint["reason"], complaint["description"]))
            flash("Warning sent to provider via email! ✅", "success")
        elif action == "dismiss":
            conn.execute("UPDATE complaints SET status='Dismissed' WHERE complaint_id=?", (complaint_id,))
            flash("Complaint dismissed.", "info")
        conn.commit()
    conn.close()
    return redirect(url_for("admin_complaints"))

def create_new_tables():
    conn = sqlite3.connect(DATABASE)
    conn.execute("CREATE TABLE IF NOT EXISTS complaints (complaint_id INTEGER PRIMARY KEY AUTOINCREMENT, booking_id INTEGER NOT NULL, user_id INTEGER NOT NULL, provider_id INTEGER NOT NULL, reason TEXT NOT NULL, description TEXT, status TEXT DEFAULT 'Pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS reschedules (reschedule_id INTEGER PRIMARY KEY AUTOINCREMENT, booking_id INTEGER NOT NULL, provider_id INTEGER NOT NULL, new_date TEXT NOT NULL, new_time TEXT NOT NULL, reason TEXT, status TEXT DEFAULT 'Pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    try: conn.execute("ALTER TABLE service_providers ADD COLUMN latitude REAL DEFAULT 28.6139")
    except: pass
    try: conn.execute("ALTER TABLE service_providers ADD COLUMN longitude REAL DEFAULT 77.2090")
    except: pass
    conn.commit()
    conn.close()

# Run init on startup always
init_db()
create_new_tables()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
