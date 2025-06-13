from flask import Flask, render_template, request, redirect, url_for, session, flash
import os

app = Flask(__name__)
# Kunci rahsia diperlukan untuk sesi Flask. Gantikan dengan rentetan yang kuat dan unik dalam produksi!
app.secret_key = os.urandom(24) 

# --- Struktur Data Sementara (akan diganti dengan interaksi Pangkalan Data Oracle) ---
# DALAM APLIKASI SEBENAR, JANGAN SIMPAN KATA LALUAN DALAM TEKS BIASA. Gunakan hashing!
users_db = {
    "guest_users": {
        "guest1": {"password": "pass1", "role": "guest", "fullname": "Ahmad Bin Abu", "email": "ahmad@example.com", "phone": "0123456789"},
        "siti": {"password": "siti123", "role": "guest", "fullname": "Siti Nurhaliza", "email": "siti@email.com", "phone": "0198765432"},
    },
    "admin_users": {
        "admin1": {"password": "adminpass", "role": "admin", "email": "admin@homestay.com"},
        "helly": {"password": "hellyadmin", "role": "admin", "email": "helly@homestay.com"},
    }
}

bookings_db = [
    {"booking_id": "B001", "guest_username": "guest1", "check_in": "2025-07-01", "check_out": "2025-07-05", "num_guests": 4, "vehicle_type": "Kereta", "status": "Disahkan"},
    {"booking_id": "B002", "guest_username": "siti", "check_in": "2025-08-10", "check_out": "2025-08-12", "num_guests": 2, "vehicle_type": "Tiada", "status": "Menunggu Pengesahan"},
]

bills_db = [
    {"bill_id": "BIL001", "booking_id": "B001", "guest_username": "guest1", "amount": 300.00, "generated_date": "2025-06-10", "status": "Dibayar"},
    {"bill_id": "BIL002", "booking_id": "B002", "guest_username": "siti", "amount": 200.00, "generated_date": "2025-08-01", "status": "Belum Dibayar"},
]

# --- Fungsi Pembantu untuk interaksi DB sementara (akan diganti dengan Oracle) ---
def get_db_connection():
    """Placeholder for Oracle DB connection."""
    return None 

def query_db(query, args=(), one=False):
    """Placeholder for querying temporary DB."""
    # Simplified logic for demonstration
    if "SELECT username, password, role FROM users WHERE username = :username" in query:
        username = args[0]
        if username in users_db["guest_users"]:
            user_data = users_db["guest_users"][username]
            return (user_data["password"], user_data["role"]) if one else [(user_data["password"], user_data["role"])]
        elif username in users_db["admin_users"]:
            user_data = users_db["admin_users"][username]
            return (user_data["password"], user_data["role"]) if one else [(user_data["password"], user_data["role"])]
    return None if one else []

def insert_db(table, data):
    """Placeholder for inserting into temporary DB."""
    if table == "guest_users":
        username = data['username']
        if username not in users_db["guest_users"]:
            users_db["guest_users"][username] = data
            return True
        return False
    elif table == "bookings":
        data['booking_id'] = f"B{len(bookings_db) + 1:03d}" 
        bookings_db.append(data)
        return True
    elif table == "bills":
        data['bill_id'] = f"BIL{len(bills_db) + 1:03d}" 
        bills_db.append(data)
        return True
    return False

def update_db(table, identifier, data):
    """Placeholder for updating temporary DB."""
    if table == "guest_users":
        username = identifier['username']
        if username in users_db["guest_users"]:
            users_db["guest_users"][username].update(data)
            return True
    elif table == "bookings":
        booking_id = identifier['booking_id']
        for i, booking in enumerate(bookings_db):
            if booking['booking_id'] == booking_id:
                bookings_db[i].update(data)
                return True
    return False

def delete_db(table, identifier):
    """Placeholder for deleting from temporary DB."""
    if table == "guest_users":
        username = identifier['username']
        if username in users_db["guest_users"]:
            del users_db["guest_users"][username]
            return True
    return False

# --- Laluan Utama (Log Masuk Tetamu) ---
@app.route('/')
def index():
    """Halaman Utama / Log Masuk Tetamu"""
    return render_template('index.html')

# --- Laluan Log Masuk Generik (digunakan oleh borang log masuk Tetamu di index.html) ---
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if username in users_db["guest_users"] and users_db["guest_users"][username]["password"] == password:
        session['logged_in'] = True
        session['username'] = username
        session['role'] = 'guest'
        flash("Berjaya log masuk sebagai Tetamu!", "success")
        return redirect(url_for('guest_home'))
    else:
        flash("Nama pengguna atau kata laluan tidak sah untuk log masuk tetamu.", "danger")
        return redirect(url_for('index'))

# --- Laluan Log Masuk Admin Khusus ---
@app.route('/login-admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users_db["admin_users"] and users_db["admin_users"][username]["password"] == password:
            session['logged_in'] = True
            session['username'] = username
            session['role'] = 'admin'
            flash("Berjaya log masuk sebagai Admin!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Nama pengguna atau kata laluan tidak sah untuk log masuk admin.", "danger")
            return render_template('login_admin.html') # Render kembali halaman log masuk admin dengan ralat
    # Untuk permintaan GET, paparkan borang log masuk admin
    return render_template('login_admin.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Anda telah log keluar.", "info")
    return redirect(url_for('index'))

# --- Laluan Tetamu ---
@app.route('/daftar-tetamu', methods=['GET', 'POST'])
def guest_registration():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        phone = request.form['phone']
        username = request.form['username']
        password = request.form['password']

        if insert_db("guest_users", {
            "username": username,
            "password": password, # Ingat: hash kata laluan dalam aplikasi sebenar!
            "role": "guest",
            "fullname": fullname,
            "email": email,
            "phone": phone
        }):
            flash("Pendaftaran berjaya! Sila log masuk.", "success")
            return redirect(url_for('index'))
        else:
            flash("Nama pengguna sudah wujud. Sila pilih nama pengguna lain.", "danger")
            return render_template('guest_registration.html', fullname=fullname, email=email, phone=phone, username=username)
    return render_template('guest_registration.html')

@app.route('/dashboard-tetamu')
def guest_home():
    if 'logged_in' in session and session['role'] == 'guest':
        username = session['username']
        guest_info = users_db["guest_users"].get(username, {})
        user_bookings = [b for b in bookings_db if b['guest_username'] == username]
        latest_booking_status = user_bookings[-1]['status'] if user_bookings else "Tiada tempahan aktif."
        return render_template('guest_home.html', guest_info=guest_info, latest_booking_status=latest_booking_status)
    flash("Sila log masuk sebagai tetamu untuk mengakses halaman ini.", "warning")
    return redirect(url_for('index'))

@app.route('/tempahan-tetamu', methods=['GET', 'POST'])
def guest_booking():
    if 'logged_in' in session and session['role'] == 'guest':
        if request.method == 'POST':
            check_in_date = request.form['check_in_date']
            check_out_date = request.form['check_out_date']
            num_guests = request.form['num_guests']
            vehicle_type = request.form.get('vehicle_type', 'Tiada')

            new_booking = {
        "guest_username": session['username'],
        "check_in": check_in_date,
        "check_out": check_out_date,
        "num_guests": int(num_guests),
        "vehicle_type": vehicle_type,
        "vehicle_plate": vehicle_plate,  # ditambah di sini
        "status": "Menunggu Pengesahan"
}
            if insert_db("bookings", new_booking):
                flash("Tempahan anda telah dihantar dan menunggu pengesahan.", "success")
                return redirect(url_for('guest_booking_history'))
            else:
                flash("Gagal membuat tempahan. Sila cuba lagi.", "danger")
                return render_template('guest_booking.html', **request.form)
        return render_template('guest_booking.html')
    flash("Sila log masuk sebagai tetamu untuk mengakses halaman ini.", "warning")
    return redirect(url_for('index'))

@app.route('/sejarah-tempahan-tetamu')
def guest_booking_history():
    if 'logged_in' in session and session['role'] == 'guest':
        username = session['username']
        user_bookings = [b for b in bookings_db if b['guest_username'] == username]
        return render_template('guest_booking_history.html', bookings=user_bookings)
    flash("Sila log masuk sebagai tetamu untuk mengakses halaman ini.", "warning")
    return redirect(url_for('index'))

@app.route('/profil-tetamu', methods=['GET', 'POST'])
def guest_profile():
    if 'logged_in' in session and session['role'] == 'guest':
        username = session['username']
        user_data = users_db["guest_users"].get(username)
        if request.method == 'POST':
            updated_data = {
                'fullname': request.form['fullname'],
                'email': request.form['email'],
                'phone': request.form['phone'],
                'username': request.form['username']
            }

            if updated_data['username'] != username and updated_data['username'] in users_db["guest_users"]:
                flash("Nama pengguna baharu sudah wujud. Sila pilih yang lain.", "danger")
                return render_template('guest_profile.html', user=user_data)

            if updated_data['username'] != username:
                # Perlu mengemaskini session username juga
                users_db["guest_users"][updated_data['username']] = users_db["guest_users"].pop(username)
                session['username'] = updated_data['username']
                username = session['username'] 

            if update_db("guest_users", {'username': username}, updated_data):
                flash("Profil anda telah berjaya dikemaskini.", "success")
            else:
                flash("Gagal mengemaskini profil.", "danger")
            user_data = users_db["guest_users"].get(username) # Refresh user_data
            return render_template('guest_profile.html', user=user_data)
        return render_template('guest_profile.html', user=user_data)
    flash("Sila log masuk sebagai tetamu untuk mengakses halaman ini.", "warning")
    return redirect(url_for('index'))

# --- Laluan Admin ---
@app.route('/dashboard-admin')
def admin_dashboard():
    if 'logged_in' in session and session['role'] == 'admin':
        num_guests = len(users_db["guest_users"])
        pending_bookings = [b for b in bookings_db if b['status'] == 'Menunggu Pengesahan']
        num_pending_bookings = len(pending_bookings)
        unpaid_bills = [b for b in bills_db if b['status'] == 'Belum Dibayar']
        num_unpaid_bills = len(unpaid_bills)
        return render_template('admin_dashboard.html',
                               num_guests=num_guests,
                               num_pending_bookings=num_pending_bookings,
                               num_unpaid_bills=num_unpaid_bills)
    flash("Sila log masuk sebagai admin untuk mengakses halaman ini.", "warning")
    return redirect(url_for('index'))

@app.route('/urus-tetamu')
def admin_guest_management():
    if 'logged_in' in session and session['role'] == 'admin':
        all_guests = users_db["guest_users"].items()
        return render_template('admin_guest_management.html', guests=all_guests)
    flash("Sila log masuk sebagai admin untuk mengakses halaman ini.", "warning")
    return redirect(url_for('index'))

@app.route('/urus-admin')
def admin_admin_management():
    if 'logged_in' in session and session['role'] == 'admin':
        all_admins = users_db["admin_users"].items()
        return render_template('admin_admin_management.html', admins=all_admins)
    flash("Sila log masuk sebagai admin untuk mengakses halaman ini.", "warning")
    return redirect(url_for('index'))

@app.route('/urus-tempahan')
def admin_booking_management():
    if 'logged_in' in session and session['role'] == 'admin':
        bookings_with_guest_names = []
        for booking in bookings_db:
            guest_username = booking['guest_username']
            guest_info = users_db['guest_users'].get(guest_username, {})
            booking_display = booking.copy()
            booking_display['guest_fullname'] = guest_info.get('fullname', guest_username)
            bookings_with_guest_names.append(booking_display)
        return render_template('admin_booking_management.html', bookings=bookings_with_guest_names)
    flash("Sila log masuk sebagai admin untuk mengakses halaman ini.", "warning")
    return redirect(url_for('index'))

@app.route('/sahkan-tempahan/<booking_id>')
def confirm_booking(booking_id):
    if 'logged_in' in session and session['role'] == 'admin':
        for booking in bookings_db:
            if booking['booking_id'] == booking_id:
                booking['status'] = 'Disahkan'
                flash(f"Tempahan {booking_id} telah disahkan.", "success")
                break
        return redirect(url_for('admin_booking_management'))
    flash("Anda tidak mempunyai kebenaran untuk melakukan tindakan ini.", "danger")
    return redirect(url_for('index'))

@app.route('/batalkan-tempahan/<booking_id>')
def cancel_booking(booking_id):
    if 'logged_in' in session and session['role'] == 'admin':
        for booking in bookings_db:
            if booking['booking_id'] == booking_id:
                booking['status'] = 'Dibatalkan'
                flash(f"Tempahan {booking_id} telah dibatalkan.", "info")
                break
        return redirect(url_for('admin_booking_management'))
    flash("Anda tidak mempunyai kebenaran untuk melakukan tindakan ini.", "danger")
    return redirect(url_for('index'))

@app.route('/urus-bil')
def admin_bill_management():
    if 'logged_in' in session and session['role'] == 'admin':
        bills_with_guest_names = []
        for bill in bills_db:
            guest_username = bill['guest_username']
            guest_info = users_db['guest_users'].get(guest_username, {})
            bill_display = bill.copy()
            bill_display['guest_fullname'] = guest_info.get('fullname', guest_username)
            bills_with_guest_names.append(bill_display)
        return render_template('admin_bill_management.html', bills=bills_with_guest_names)
    flash("Sila log masuk sebagai admin untuk mengakses halaman ini.", "warning")
    return redirect(url_for('index'))

@app.route('/tandakan-dibayar/<bill_id>')
def mark_bill_paid(bill_id):
    if 'logged_in' in session and session['role'] == 'admin':
        for bill in bills_db:
            if bill['bill_id'] == bill_id:
                bill['status'] = 'Dibayar'
                flash(f"Bil {bill_id} telah ditandakan sebagai dibayar.", "success")
                break
        return redirect(url_for('admin_bill_management'))
    flash("Anda tidak mempunyai kebenaran untuk melakukan tindakan ini.", "danger")
    return redirect(url_for('index'))

@app.route('/jana-bil-baru')
def generate_new_bill():
    if 'logged_in' in session and session['role'] == 'admin':
        flash("Fungsi jana bil baharu akan ditambah di sini.", "info")
        return redirect(url_for('admin_bill_management'))
    flash("Sila log masuk sebagai admin untuk mengakses halaman ini.", "warning")
    return redirect(url_for('index'))

if __name__ == '__main__':
    # use_reloader=False is set to prevent OSError: [WinError 10038] on Windows
    # This means you'll need to manually restart the server after code changes.
    app.run(debug=True, port=5000, use_reloader=False)