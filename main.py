from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

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

def query_bookings():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM BOOKING")
        results = cursor.fetchall()
        for row in results:
            print(row)
        cursor.close()
        conn.close()
    except Exception as e:
        print("❌ Query failed:", e)

# --- Fungsi Pembantu untuk interaksi DB sementara (akan diganti dengan Oracle) ---
def get_db_connection():
    dsn = oracledb.makedsn("localhost", 1521, service_name="FREEPDB1")
    return oracledb.connect(
        user="system",
        password="Admin#123",
        dsn=dsn
    )
    return conn
try:
    conn = get_db_connection()
    cur = conn.cursor()
    # do queries
except oracledb.DatabaseError as e:
    error, = e.args
    print(f"❌ Oracle DB Error: {error.message}")
finally:
    try:
        cur.close()
        conn.close()
    except:
        pass

# try:
#     conn = get_db_connection()
#     print("✅ Connected to Oracle DB")
# except Exception as e:
#     print("❌ Connection failed:", e)




def query_db(query, args=(), one=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(query, args)
    rows = cursor.fetchall()
    
    # Optional: Convert to list of dicts
    columns = [col[0] for col in cursor.description]
    result = [dict(zip(columns, row)) for row in rows]

    cursor.close()
    conn.close()

    if one:
        return result[0] if result else None
    return result



def insert_db(query, args=()):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    cursor.close()
    conn.close()



def update_db(query, args=()):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    cursor.close()
    conn.close()


def delete_db(query, args=()):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    cursor.close()
    conn.close()


def select_db(table, condition=None):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if table == "Guest":
            query = "SELECT * FROM Guest"
            params = ()

            if condition and 'GuestID' in condition:
                query += " WHERE GuestID = :1"
                params = (condition['GuestID'],)

        elif table == "Booking":
            query = "SELECT * FROM Booking"
            params = ()

            if condition and 'BookingID' in condition:
                query += " WHERE BookingID = :1"
                params = (condition['BookingID'],)

        elif table == "Bill":
            query = "SELECT * FROM Bill"
            params = ()

            if condition and 'BillID' in condition:
                query += " WHERE BillID = :1"
                params = (condition['BillID'],)

        else:
            print(f"Table '{table}' is not supported.")
            return []

        cur.execute(query, params)
        rows = cur.fetchall()
        return rows

    except Exception as e:
        print("DB Select Error:", e)
        return []

    finally:
        cur.close()

def search_all(name=None, status=None, date=None):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        query = """
            SELECT 
                g.GuestID, g.FullName, g.PhoneNo,
                b.BookingID, b.CheckInDate, b.CheckOutDate, b.Status AS BookingStatus,
                bi.BillID, bi.Amount, bi.IssuedDate, bi.Status AS BillStatus
            FROM Guest g
            LEFT JOIN Booking b ON g.GuestID = b.GuestID
            LEFT JOIN Bill bi ON b.BookingID = bi.BookingID
            WHERE 1=1
        """
        params = []

        if name:
            query += " AND LOWER(g.FullName) LIKE LOWER(:{})".format(len(params)+1)
            params.append(f"%{name}%")

        if status:
            query += " AND (LOWER(b.Status) = LOWER(:{}) OR LOWER(bi.Status) = LOWER(:{}))".format(len(params)+1, len(params)+2)
            params.extend([status.lower(), status.lower()])

        if date:
            query += " AND (TO_CHAR(b.CheckInDate, 'YYYY-MM-DD') = :{} OR TO_CHAR(bi.IssuedDate, 'YYYY-MM-DD') = :{})".format(len(params)+1, len(params)+2)
            params.extend([date, date])

        cur.execute(query, params)
        rows = cur.fetchall()

        result = []
        for row in rows:
            result.append({
                "GuestID": row[0],
                "FullName": row[1],
                "PhoneNo": row[2],
                "BookingID": row[3],
                "CheckInDate": row[4].strftime('%Y-%m-%d') if row[4] else None,
                "CheckOutDate": row[5].strftime('%Y-%m-%d') if row[5] else None,
                "BookingStatus": row[6],
                "BillID": row[7],
                "Amount": float(row[8]) if row[8] is not None else None,
                "IssuedDate": row[9].strftime('%Y-%m-%d') if row[9] else None,
                "BillStatus": row[10]
            })

        return result

    except Exception as e:
        print("Search Error:", e)
        return []

    finally:
        cur.close()

@app.route('/test-db')
def test_db():
    try:
        rows = query_db("SELECT * FROM dual")
        return f"Connected! Oracle responded: {rows}"
    except Exception as e:
        return f"DB error: {str(e)}"

# --- Laluan Utama (Log Masuk Tetamu) ---
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT * FROM GUEST WHERE USERNAME = :1", (username,))
            guest_data = cur.fetchone()

            if guest_data:
                db_password = guest_data[4]
                if check_password_hash(db_password, password):
                    session['logged_in'] = True
                    session['username'] = username
                    session['role'] = 'guest'
                    flash("Berjaya log masuk!", "success")
                    return redirect(url_for('guest_home'))
                else:
                    flash("Kata laluan salah", "danger")
            else:
                flash("Nama pengguna tidak dijumpai", "danger")

        except Exception as e:
            print("Error login:", e)
            flash("Ralat sistem", "danger")

        finally:
            cur.close()
            conn.close()

        return redirect(url_for('index'))

    return render_template('index.html')


# --- Laluan Log Masuk Admin Khusus ---
@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    
    if 'logged_in' in session and session['role'] == 'admin':
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT * FROM ADMIN WHERE USERNAME = :1", (username,))
            admin_data = cur.fetchone()
            print("ADMIN DATA:", admin_data)  # 👈 print for debug

            if admin_data:
                db_password = admin_data[2]  # pastikan index betul
                print("DB PASSWORD:", db_password)
                # check plain text
                if password == db_password:
                    session['logged_in'] = True
                    session['role'] = 'admin'
                    session['username'] = username
                    flash("Berjaya log masuk sebagai admin!", "success")
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash("Kata laluan salah.", "danger")
            else:
                flash("Nama pengguna tidak dijumpai.", "danger")

        except Exception as e:
            flash("Ralat log masuk admin: " + str(e), "danger")

        finally:
            if cur:
                cur.close()
            conn.close()

    return render_template('login_admin.html')



@app.route('/logout')
def logout():
    session.clear()
    flash("Anda telah log keluar.", "info")
    return redirect(url_for('index'))

# --- Laluan Tetamu ---
from werkzeug.security import generate_password_hash

@app.route('/guest/guest_registration', methods=['GET', 'POST'])
def guest_registration():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        phone = request.form['phone']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Kata laluan dan pengesahan tidak sepadan.", "danger")
            return render_template('guest/guest_registration.html', fullname=fullname, email=email, phone=phone, username=username)

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM GUEST WHERE Username = :1", (username,))
        existing_user = cur.fetchone()

        if existing_user:
            flash("Nama pengguna sudah wujud. Sila pilih nama pengguna lain.", "danger")
            return render_template('guest/guest_registration.html', fullname=fullname,email=email, phone=phone, username=username)

        hashed_password = generate_password_hash(password)

        try:
            cur.execute("""
                INSERT INTO GUEST (FullName,  Email, PhoneNo, Username, GPassword)
                VALUES (:1, :2, :3, :4, :5)
            """, (fullname, email, phone, username, hashed_password))

            conn.commit()
            flash("Pendaftaran berjaya! Sila log masuk.", "success")
            return redirect(url_for('index'))

        except Exception as e:
            print("Insert Error:", e)
            flash("Pendaftaran gagal. Sila cuba lagi.", "danger")
            return render_template('guest/guest_registration.html', fullname=fullname, email=email, phone=phone, username=username)

        finally:
            cur.close()
            conn.close()

    return render_template('guest/guest_registration.html')



@app.route('/guest/guest_home')
def guest_home():
    print("DEBUG: Session inside /guest/guest_home →", session)

    if 'logged_in' in session and session.get('role') == 'guest':
        username = session.get('username')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Ambil tempahan terbaru untuk pengguna ini
            cur.execute("""
                SELECT B.BOOKINGID, B.STATUS
                FROM BOOKING B
                JOIN GUEST G ON B.GUESTID = G.GUESTID
                WHERE G.USERNAME = :1
                ORDER BY B.CHECKINDATE DESC FETCH FIRST 1 ROWS ONLY
            """, (username,))

            bookings = []
            row = cur.fetchone()
            if row:
                bookings.append({
                    "booking_id": row[0],
                    "status": row[1]
                })

            return render_template('guest/guest_home.html', username=username, booking=bookings)

        except Exception as e:
            flash("Ralat sistem semasa memuatkan dashboard: " + str(e), "danger")
            return redirect(url_for('index'))

        finally:
            cur.close()
            conn.close()
    
    flash("Sila log masuk dahulu.", "warning")
    return redirect(url_for('index'))


@app.route('/guest/guest_booking', methods=['GET', 'POST'])
def guest_booking():
    if 'logged_in' in session and session['role'] == 'guest':
        if request.method == 'POST':
            check_in_date = request.form['check_in_date']
            check_out_date = request.form['check_out_date']
            num_guests = int(request.form['num_guests'])
            extra_hours = int(request.form.get('extra_hours', 0))

            username = session['username']
            try:
                conn = get_db_connection()
                cur = conn.cursor()

                # Step 1: Get GUESTID
                cur.execute("SELECT GUESTID FROM GUEST WHERE USERNAME = :1", (username,))
                guest_id = cur.fetchone()[0]

                # Step 2: Calculate nights
                from datetime import datetime
                check_in_dt = datetime.strptime(check_in_date, '%Y-%m-%d')
                check_out_dt = datetime.strptime(check_out_date, '%Y-%m-%d')
                nights = (check_out_dt - check_in_dt).days

                if nights <= 0:
                    flash("Tarikh keluar mesti selepas tarikh masuk.", "warning")
                    return render_template('guest/guest_booking.html', **request.form)

                # Step 3: Calculate price
                price_per_night = 100
                price_per_extra_hour = 20
                total_price = (nights * price_per_night) + (extra_hours * price_per_extra_hour)

                # Step 4: Insert
                cur.execute("""
                    INSERT INTO BOOKING (
                        GUESTID, CHECKINDATE, CHECKOUTDATE, NUMOFGUESTS, EXTRAHOURS, TOTALPRICE, STATUS
                    )
                    VALUES (
                        :1, TO_DATE(:2, 'YYYY-MM-DD'), TO_DATE(:3, 'YYYY-MM-DD'), :4, :5, :6, :7
                    )
                """, (
                    guest_id,
                    check_in_date,
                    check_out_date,
                    num_guests,
                    extra_hours,
                    total_price,
                    'Menunggu Pengesahan'
                ))
                conn.commit()

                flash(f"Tempahan berjaya. Jumlah harga: RM{total_price:.2f}", "success")
                return redirect(url_for('guest_booking'))

            except Exception as e:
                conn.rollback()
                flash("Gagal membuat tempahan. Ralat: " + str(e), "danger")
                return render_template('guest/guest_booking.html', **request.form)

            finally:
                cur.close()
                conn.close()

        return render_template('guest/guest_booking.html')

    flash("Sila log masuk sebagai tetamu untuk mengakses halaman ini.", "warning")
    return redirect(url_for('index'))




from datetime import datetime
from flask import session, redirect, url_for, render_template, flash

@app.route('/guest/guest_booking_history')
def guest_booking_history():
    print("DEBUG: Session inside /guest/guest_booking_history →", session)
    print("SESSION DEBUG:", dict(session))

    if 'logged_in' in session and session['role'] == 'guest':
        username = session['username']
        rate_per_night = 100  # Harga semalam (boleh ubah ikut kehendak)

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT B.BOOKINGID, B.CHECKINDATE, B.CHECKOUTDATE, B.NUMOFGUESTS, B.STATUS
                FROM BOOKING B
                JOIN GUEST G ON B.GUESTID = G.GUESTID
                WHERE G.USERNAME = :1
                ORDER BY B.CHECKINDATE DESC
            """, (username,))
            booking = []

            for row in cur.fetchall():
                check_in = row[1] if isinstance(row[1], datetime) else datetime.strptime(row[1], '%Y-%m-%d')
                check_out = row[2] if isinstance(row[2], datetime) else datetime.strptime(row[2], '%Y-%m-%d')
                num_nights = (check_out - check_in).days
                total_price = num_nights * rate_per_night

                booking.append({
                    "booking_id": row[0],
                    "check_in": check_in.strftime('%Y-%m-%d'),
                    "check_out": check_out.strftime('%Y-%m-%d'),
                    "num_guests": row[3],
                    "status": row[4],
                    "total_price": total_price
                })

            return render_template('guest/guest_booking_history.html', booking=booking)

        except Exception as e:
            flash("Ralat mendapatkan sejarah tempahan: " + str(e), "danger")
            return redirect(url_for('index'))

        finally:
            cur.close()
            conn.close()

    flash("Sila log masuk sebagai tetamu untuk mengakses halaman ini.", "warning")
    return redirect(url_for('index'))



@app.route('/guest/guest_profile', methods=['GET', 'POST'])
def guest_profile():
    if 'logged_in' in session and session['role'] == 'guest':
        username = session['username']
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            if request.method == 'POST':
                updated_data = {
                    'fullname': request.form['fullname'],
                    'email': request.form['email'],
                    'phoneno': request.form['phone'],
                    'username': request.form['username']
                }

                # Check kalau username baru dah wujud
                if updated_data['username'] != username:
                    cur.execute("SELECT * FROM GUEST WHERE USERNAME = :1", (updated_data['username'],))
                    if cur.fetchone():
                        flash("Nama pengguna baharu sudah wujud. Sila pilih yang lain.", "danger")
                        return redirect(url_for('guest_profile'))

                # Update data
                cur.execute("""
                    UPDATE GUEST
                    SET FULLNAME = :1, EMAIL = :2, PHONENO = :3, USERNAME = :4
                    WHERE USERNAME = :5
                """, (updated_data['fullname'], updated_data['email'], updated_data['phoneno'], updated_data['username'], username))

                conn.commit()

                # Update session jika username berubah
                if updated_data['username'] != username:
                    session['username'] = updated_data['username']

                flash("Profil anda telah berjaya dikemaskini.", "success")

            # Dapatkan data semasa
            cur.execute("SELECT FULLNAME, EMAIL, PHONENO, USERNAME FROM GUEST WHERE USERNAME = :1", (session['username'],))
            row = cur.fetchone()
            user_data = {
                'fullname': row[0],
                'email': row[1],
                'phone': row[2],
                'username': row[3]
            }

            return render_template('guest/guest_profile.html', user=user_data)

        except Exception as e:
            flash("Ralat: " + str(e), "danger")
            return redirect(url_for('guest_profile'))

        finally:
            cur.close()
            conn.close()

    flash("Sila log masuk sebagai tetamu untuk mengakses halaman ini.", "warning")
    return redirect(url_for('index'))




@app.route('/admin/admin_dashboard')
def admin_dashboard():
    if 'logged_in' in session and session['role'] == 'admin':
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM GUEST")
            num_guests = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM BOOKING WHERE STATUS = 'Menunggu Pengesahan'")
            num_pending_bookings = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM BILL WHERE STATUS != 'Telah Dibayar'")
            num_unpaid_bills = cur.fetchone()[0]

            # print("DEBUG: Guests =", num_guests)
            # print("DEBUG: Pending bookings =", num_pending_bookings)
            # print("DEBUG: Unpaid bills =", num_unpaid_bills)

            return render_template(
                'admin/admin_dashboard.html',
                num_guests=num_guests,
                num_pending_bookings=num_pending_bookings,
                num_unpaid_bills=num_unpaid_bills
            )

        except Exception as e:
            flash(f"Ralat dashboard: {str(e)}", "danger")
        finally:
            cur.close()
            conn.close()

    flash("Sila log masuk sebagai admin.", "warning")
    return redirect(url_for('index'))


@app.route('/admin/admin_guest_management')
def admin_guest_management():
    if 'logged_in' in session and session['role'] == 'admin':
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT GUESTID, FULLNAME, EMAIL, PHONENO, USERNAME FROM GUEST")
            guest = cur.fetchall()
            return render_template('admin/admin_guest_management.html', guest=guest)
        except Exception as e:
            flash(f"Ralat semasa akses tetamu: {e}", "danger")
            return redirect(url_for('admin_dashboard'))
        finally:
            cur.close()
            conn.close()
    flash("Sila log masuk sebagai admin untuk mengakses halaman ini.", "warning")
    return redirect(url_for('index'))

@app.route('/admin/kemaskini-tetamu/<int:guest_id>', methods=['GET', 'POST'])
def kemaskini_tetamu(guest_id):
    if 'logged_in' in session and session['role'] == 'admin':
        conn = get_db_connection()
        cur = conn.cursor()

        if request.method == 'POST':
            try:
                fullname = request.form.get('fullname')
                email = request.form.get('email')
                phone = request.form.get('phone')
                username = request.form.get('username')

                cur.execute("""
                    UPDATE GUEST 
                    SET FULLNAME=:1, EMAIL=:2, PHONENO=:3, USERNAME=:4 
                    WHERE GUESTID=:5
                """, (fullname, email, phone, username, guest_id))
                conn.commit()
                flash("Butiran tetamu berjaya dikemaskini!", "success")
                return redirect(url_for('admin_guest_management'))
            except Exception as e:
                flash(f"Ralat semasa mengemaskini: {e}", "danger")
                return redirect(url_for('admin_guest_management'))
            finally:
                cur.close()
                conn.close()

        else:  # GET
            try:
                cur.execute("SELECT * FROM GUEST WHERE GUESTID = :1", (guest_id,))
                guest = cur.fetchone()
                if guest:
                    return render_template('admin/edit_guest.html', guest=guest)
                else:
                    flash("Tetamu tidak dijumpai.", "warning")
                    return redirect(url_for('admin_guest_management'))
            finally:
                cur.close()
                conn.close()
    else:
        flash("Sila log masuk sebagai admin.", "warning")
        return redirect(url_for('index'))


@app.route('/admin/padam-tetamu/<int:guest_id>', methods=['POST'])
def padam_tetamu(guest_id):
    if 'logged_in' in session and session['role'] == 'admin':
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM GUEST WHERE GUESTID = :1", (guest_id,))
            conn.commit()
            flash("Tetamu berjaya dipadam.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Ralat semasa memadam tetamu: {e}", "danger")
        finally:
            cur.close()
            conn.close()
        return redirect(url_for('admin_guest_management'))

    flash("Sila log masuk sebagai admin.", "warning")
    return redirect(url_for('index'))




@app.route('/admin/admin_admin_management')
def admin_admin_management():
    if 'logged_in' in session and session['role'] == 'admin':
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT ADMINID, USERNAME FROM ADMIN ORDER BY ADMINID")
            admins = cur.fetchall()

            cur.close()
            conn.close()

            return render_template('admin/admin_admin_management.html', admins=admins)

        except Exception as e:
            flash("Ralat semasa akses admin: " + str(e), "danger")
            return redirect(url_for('admin_dashboard'))

    flash("Sila log masuk sebagai admin untuk mengakses halaman ini.", "warning")
    return redirect(url_for('index'))


@app.route('/admin/tambah_admin')
def show_add_admin_form():
    if 'logged_in' in session and session['role'] == 'admin':
        return render_template(
            'admin/admin_form.html',
            mode='Daftar',
            action_url=url_for('add_admin'),
            admin=None
        )
    flash("Sila log masuk sebagai admin.", "warning")
    return redirect(url_for('index'))


@app.route('/admin/tambah_admin', methods=['POST'])
def add_admin():
    if 'logged_in' in session and session['role'] == 'admin':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO ADMIN (USERNAME, PASSWORD) VALUES (:1, :2)", (username, password))
            conn.commit()
            flash("Admin berjaya ditambah!", "success")
        except Exception as e:
            flash("Ralat tambah admin: " + str(e), "danger")
        finally:
            cur.close()
            conn.close()
        return redirect(url_for('admin_admin_management'))
    flash("Sila log masuk sebagai admin.", "warning")
    return redirect(url_for('index'))

@app.route('/admin/kemaskini_admin/<int:admin_id>')
def edit_admin(admin_id):
    if 'logged_in' in session and session['role'] == 'admin':
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT ADMINID, USERNAME FROM ADMIN WHERE ADMINID = :1", (admin_id,))
            row = cur.fetchone()
            if row:
                admin = {'id': row[0], 'username': row[1]}
                return render_template(
                    'admin/admin_form.html',
                    mode='Kemaskini',
                    action_url=url_for('update_admin', admin_id=admin_id),
                    admin=admin
                )
            else:
                flash("Admin tidak dijumpai.", "warning")
        except Exception as e:
            flash("Ralat: " + str(e), "danger")
        finally:
            cur.close()
            conn.close()
    return redirect(url_for('index'))


@app.route('/admin/kemaskini_admin/<int:admin_id>', methods=['POST'])
def update_admin(admin_id):
    if 'logged_in' in session and session['role'] == 'admin':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE ADMIN SET USERNAME = :1, PASSWORD = :2 WHERE ADMINID = :3", (username, password, admin_id))
            conn.commit()
            flash("Admin dikemaskini.", "success")
        except Exception as e:
            flash("Ralat kemaskini: " + str(e), "danger")
        finally:
            cur.close()
            conn.close()
        return redirect(url_for('admin_admin_management'))
    return redirect(url_for('index'))

@app.route('/admin/delete_admin', methods=['POST'])
def delete_admin():
    if 'logged_in' in session and session['role'] == 'admin':
        admin_id = request.form['admin_id']
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM ADMIN WHERE ADMINID = :1", (admin_id,))
            conn.commit()
            flash("Admin dipadam.", "success")
        except Exception as e:
            flash("Ralat padam admin: " + str(e), "danger")
        finally:
            cur.close()
            conn.close()
        return redirect(url_for('admin_admin_management'))
    return redirect(url_for('index'))


@app.route('/admin/admin_booking_management') 
def admin_booking_management():
    print("DEBUG: Session inside /admin/admin_booking_management →", session)
    if 'logged_in' in session and session['role'] == 'admin':
        cur = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Join table GUESTS dan BOOKING
            cur.execute("""
                SELECT 
                    B.BOOKINGID, 
                    G.FULLNAME, 
                    B.CHECKINDATE, 
                    B.CHECKOUTDATE, 
                    B.NUMOFGUESTS, 
                    B.STATUS
                FROM 
                    BOOKING B
                JOIN 
                    GUEST G ON B.GUESTID = G.GUESTID
                ORDER BY B.CHECKINDATE DESC
            """)
            bookings_data = cur.fetchall()

            bookings = []
            for row in bookings_data:
                bookings.append({
                    'id': row[0],
                    'name': row[1],
                    'checkin': row[2],
                    'checkout': row[3],
                    'guests': row[4],
                    'status': row[5]
                })

            return render_template('admin/admin_booking_management.html', bookings=bookings)

        except Exception as e:
            flash("Ralat semasa akses tempahan: " + str(e), "danger")
            return redirect(url_for('admin_dashboard'))

        finally:
            if cur:
                cur.close()
            conn.close()

    flash("Sila log masuk sebagai admin untuk mengakses halaman ini.", "warning")
    return redirect(url_for('index'))



@app.route('/sahkan-tempahan/<booking_id>')
def confirm_booking(booking_id):
    if 'logged_in' in session and session['role'] == 'admin':
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # 1. Update status tempahan
            cur.execute("""
                UPDATE BOOKING SET STATUS = 'Disahkan' WHERE BOOKINGID = :1
            """, (booking_id,))

            # 2. Dapatkan details tempahan
            cur.execute("""
                SELECT CHECKINDATE, CHECKOUTDATE, TOTALPRICE 
                FROM BOOKING WHERE BOOKINGID = :1
            """, (booking_id,))
            booking = cur.fetchone()

            if not booking:
                flash("Tempahan tidak dijumpai untuk jana bil.", "danger")
                return redirect(url_for('admin_booking_management'))

            checkin = booking[0]
            checkout = booking[1]
            total_amount = booking[2]  # ✅ Gunakan terus TOTALPRICE

            # 3. Insert ke dalam BILL jika belum wujud
            cur.execute("SELECT * FROM BILL WHERE BOOKINGID = :1", (booking_id,))
            existing_bill = cur.fetchone()

            if not existing_bill:
                cur.execute("""
                    INSERT INTO BILL (BOOKINGID, AMOUNT, ISSUEDDATE, STATUS)
                    VALUES (:1, :2, SYSDATE, 'Belum Dibayar')
                """, (booking_id, total_amount))

            conn.commit()
            flash(f"Tempahan {booking_id} disahkan dan bil telah dijana (RM{total_amount:.2f}).", "success")

        except Exception as e:
            flash(f"Ralat semasa pengesahan: {str(e)}", "danger")

        finally:
            cur.close()
            conn.close()

        return redirect(url_for('admin_booking_management'))

    flash("Anda tidak mempunyai kebenaran untuk tindakan ini.", "danger")
    return redirect(url_for('index'))



@app.route('/batalkan-tempahan/<booking_id>')
def cancel_booking(booking_id):
    if 'logged_in' in session and session['role'] == 'admin':
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Update status ke 'Dibatalkan'
            cur.execute("""
                UPDATE BOOKING SET STATUS = 'Dibatalkan' WHERE BOOKINGID = :1
            """, (booking_id,))

            conn.commit()
            flash(f"Tempahan {booking_id} telah dibatalkan.", "info")

        except Exception as e:
            flash(f"Ralat semasa membatalkan: {str(e)}", "danger")

        finally:
            cur.close()
            conn.close()

        return redirect(url_for('admin_booking_management'))

    flash("Anda tidak mempunyai kebenaran untuk melakukan tindakan ini.", "danger")
    return redirect(url_for('index'))


@app.route('/admin/admin_bill_management')
def admin_bill_management():
    if 'logged_in' in session and session['role'] == 'admin':
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT 
                    B.BILLID, 
                    B.BOOKINGID, 
                    G.FULLNAME,
                    B.AMOUNT, 
                    TO_CHAR(B.ISSUEDDATE, 'DD-MM-YYYY'), 
                    B.STATUS
                FROM 
                    BILL B
                JOIN 
                    BOOKING BK ON B.BOOKINGID = BK.BOOKINGID
                JOIN 
                    GUEST G ON BK.GUESTID = G.GUESTID
                ORDER BY B.ISSUEDDATE DESC
            """)
            bills = cur.fetchall()

            return render_template('admin/admin_bill_management.html', bills=bills)

        except Exception as e:
            flash("Ralat semasa akses bil: " + str(e), "danger")

        finally:
            cur.close()
            conn.close()

    flash("Sila log masuk sebagai admin untuk akses halaman ini.", "warning")
    return redirect(url_for('index'))

@app.route('/tandakan-dibayar/<bill_id>')
def mark_bill_paid_get(bill_id):
    if 'logged_in' in session and session['role'] == 'admin':
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE BILL SET STATUS = 'Dibayar' WHERE BILLID = :1
            """, (bill_id,))
            conn.commit()
            flash(f"Bil #{bill_id} telah ditandakan sebagai 'Dibayar'.", "success")

        except Exception as e:
            flash("Ralat semasa mengemaskini bil: " + str(e), "danger")

        finally:
            cur.close()
            conn.close()

        return redirect(url_for('admin_bill_management'))

    flash("Akses tidak dibenarkan.", "danger")
    return redirect(url_for('index'))

@app.route('/admin/tandakan-bil-dibayar', methods=['POST'])
def mark_bill_as_paid():
    if 'logged_in' in session and session['role'] == 'admin':
        bill_id = request.form.get('bill_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("UPDATE BILL SET STATUS = 'Telah Dibayar' WHERE BILLID = :1", (bill_id,))
            conn.commit()
            flash(f"Bil #{bill_id} telah ditandakan sebagai 'Telah Dibayar'.", "success")

        except Exception as e:
            flash(f"Ralat ketika menandakan bil: {str(e)}", "danger")
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('admin_bill_management'))

    flash("Sila log masuk sebagai admin untuk akses.", "warning")
    return redirect(url_for('index'))

@app.route('/lihat-bil/<int:bill_id>', methods=['POST'])
def view_bill(bill_id):
    if 'logged_in' in session and session['role'] == 'admin':
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT 
                    B.BILLID,
                    B.BOOKINGID,
                    G.FULLNAME,
                    B.AMOUNT,
                    TO_CHAR(B.ISSUEDDATE, 'DD-MM-YYYY'),
                    B.STATUS
                FROM BILL B
                JOIN BOOKING BK ON B.BOOKINGID = BK.BOOKINGID
                JOIN GUEST G ON BK.GUESTID = G.GUESTID
                WHERE B.BILLID = :1
            """, (bill_id,))
            bill = cur.fetchone()

            if bill:
                return render_template('admin/view_single_bill.html', bill=bill)
            else:
                flash("Bil tidak dijumpai.", "danger")
                return redirect(url_for('admin_bill_management'))

        except Exception as e:
            flash(f"Ralat: {str(e)}", "danger")
        finally:
            cur.close()
            conn.close()

    flash("Sila log masuk sebagai admin.", "warning")
    return redirect(url_for('index'))



# Route for displaying the form to add a new guest
@app.route('/tambah-tetamu-manual', methods=['GET', 'POST'])
def tambah_tetamu_manual():
    # You might want to add a login check here
    if 'logged_in' not in session or session['role'] != 'admin':
        flash('Sila log masuk sebagai admin untuk mengakses halaman ini.', 'danger')
        return redirect(url_for('login_admin')) # Assuming 'login_admin' is your admin login route

    if request.method == 'POST':
        # This block handles the form submission when a new guest is registered
        guest_id = request.form['guest_id'] # Assuming you have an input for guest_id
        fullname = request.form['fullname']
        email = request.form['email']
        phoneno = request.form['phoneno']
        username = request.form['username']
        password = request.form['password'] # Remember to hash passwords in a real app!

        try:
            # Connect to your Oracle database
            # Example using cx_Oracle (replace with your actual connection logic)
            # conn = oracle_db_connect()
            # cursor = conn.cursor()
            # cursor.execute("INSERT INTO GUEST (GUESTID, FULLNAME, EMAIL, PHONENO, USERNAME, PASSWORD) VALUES (:1, :2, :3, :4, :5, :6)",
            #                (guest_id, fullname, email, phoneno, username, password))
            # conn.commit()
            # cursor.close()
            # conn.close()

            flash('Tetamu berjaya didaftarkan!', 'success')
            return redirect(url_for('admin_guest_management')) # Redirect back to guest list
        except Exception as e:
            flash(f'Ralat semasa pendaftaran tetamu: {str(e)}', 'danger')
            # You might want to log the full error for debugging
            print(f"Error registering guest: {e}")

    # This block handles the GET request to display the form
    return render_template('tambah_tetamu_manual.html')

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
    print("🚀 Testing Oracle DB Query:")
    query_bookings()
    # use_reloader=False is set to prevent OSError: [WinError 10038] on Windows
    # This means you'll need to manually restart the server after code changes.
    app.run(debug=True, port=5000, use_reloader=False)