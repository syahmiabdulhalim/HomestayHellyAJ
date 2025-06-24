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
# users_db = {
#     "guest_users": {
#         "guest1": {"password": "pass1", "role": "guest", "fullname": "Ahmad Bin Abu", "email": "ahmad@example.com", "phone": "0123456789"},
#         "siti": {"password": "siti123", "role": "guest", "fullname": "Siti Nurhaliza", "email": "siti@email.com", "phone": "0198765432"},
#     },
#     "admin_users": {
#         "admin1": {"password": "adminpass", "role": "admin", "email": "admin@homestay.com"},
#         "helly": {"password": "hellyadmin", "role": "admin", "email": "helly@homestay.com"},
#     }
# }

# bookings_db = [
#     {"booking_id": "B001", "guest_username": "guest1", "check_in": "2025-07-01", "check_out": "2025-07-05", "num_guests": 4, "vehicle_type": "Kereta", "status": "Disahkan"},
#     {"booking_id": "B002", "guest_username": "siti", "check_in": "2025-08-10", "check_out": "2025-08-12", "num_guests": 2, "vehicle_type": "Tiada", "status": "Menunggu Pengesahan"},
# ]

# bills_db = [
#     {"bill_id": "BIL001", "booking_id": "B001", "guest_username": "guest1", "amount": 300.00, "generated_date": "2025-06-10", "status": "Dibayar"},
#     {"bill_id": "BIL002", "booking_id": "B002", "guest_username": "siti", "amount": 200.00, "generated_date": "2025-08-01", "status": "Belum Dibayar"},
# ]

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
    conn = oracledb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dsn=os.getenv("DB_DSN")
    )
    return conn
try:
    conn = get_db_connection()
    print("✅ Connected to Oracle DB")
except Exception as e:
    print("❌ Connection failed:", e)




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
        phone = request.form['phone']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']

        if password != confirm_password:
            flash("Kata laluan dan pengesahan tidak sepadan.", "danger")
            return render_template('guest/guest_registration.html', fullname=fullname, phone=phone, username=username, email=email)

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM GUEST WHERE Username = :1", (username,))
        existing_user = cur.fetchone()

        if existing_user:
            flash("Nama pengguna sudah wujud. Sila pilih nama pengguna lain.", "danger")
            return render_template('guest/guest_registration.html', fullname=fullname, phone=phone, username=username, email=email)

        hashed_password = generate_password_hash(password)

        try:
            cur.execute("""
                INSERT INTO GUEST (FullName, PhoneNo, Username, GPassword, Email)
                VALUES (:1, :2, :3, :4, :5)
            """, (fullname, phone, username, hashed_password, email))

            conn.commit()
            flash("Pendaftaran berjaya! Sila log masuk.", "success")
            return redirect(url_for('index'))

        except Exception as e:
            print("Insert Error:", e)
            flash("Pendaftaran gagal. Sila cuba lagi.", "danger")
            return render_template('guest/guest_registration.html', fullname=fullname, phone=phone, username=username, email=email)

        finally:
            cur.close()
            conn.close()

    return render_template('guest/guest_registration.html')



@app.route('/guest/guest_home')
def guest_home():
    print("DEBUG: Session inside /guest/guest_home →", session)
    if 'logged_in' in session and session.get('role') == 'guest':
        return render_template('guest/guest_home.html', username=session.get('username'))
    else:
        flash("Sila log masuk dahulu.", "warning")
        return redirect(url_for('index'))

@app.route('/guest/guest_booking', methods=['GET', 'POST'])
def guest_booking():
    if 'logged_in' in session and session['role'] == 'guest':
        if request.method == 'POST':
            check_in_date = request.form['check_in_date']
            check_out_date = request.form['check_out_date']
            num_guests = request.form['num_guests']

            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO BOOKINGS (GUESTID, CHECKINDATE, CHECKOUTDATE, NUMOFGUESTS, STATUS)
                    VALUES (
                        (SELECT GUESTID FROM GUEST WHERE USERNAME = :1),
                        TO_DATE(:2, 'YYYY-MM-DD'),
                        TO_DATE(:3, 'YYYY-MM-DD'),
                        :4,
                        :5
                    )
                """, (
                    session['username'],
                    check_in_date,
                    check_out_date,
                    num_guests,
                    'Menunggu Pengesahan'
                ))
                conn.commit()
                flash("Tempahan anda telah dihantar dan menunggu pengesahan.", "success")
                return redirect(url_for('guest_booking_history'))

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

@app.route('/guest/guest_booking_history')
def guest_booking_history():
    print("DEBUG: Session inside /guest/guest_booking_history →", session)

    if 'logged_in' in session and session['role'] == 'guest':
        username = session['username']

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT B.BOOKINGID, B.CHECKINDATE, B.CHECKOUTDATE, B.NUMOFGUESTS, B.STATUS
                FROM BOOKINGS B
                JOIN GUEST G ON B.GUESTID = G.GUESTID
                WHERE G.USERNAME = :1
                ORDER BY B.CHECKINDATE DESC
            """, (username,))
            bookings = []
            for row in cur.fetchall():
                bookings.append({
                    "booking_id": row[0],
                    "check_in": row[1] if isinstance(row[1], datetime) else datetime.strptime(row[1], '%Y-%m-%d'),
                    "check_out": row[2] if isinstance(row[2], datetime) else datetime.strptime(row[2], '%Y-%m-%d'),
                    "num_guests": row[3],
                    "status": row[4]
                })

            return render_template('guest/guest_booking_history.html', bookings=bookings)

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


from werkzeug.security import check_password_hash

@app.route('/log-masuk-tetamu', methods=['GET', 'POST'])
def login_guest():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Cari tetamu ikut username
            cur.execute("SELECT GuestID, FullName, GPassword FROM GUEST WHERE Username = :1", (username,))
            user = cur.fetchone()

            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = username
                session['role'] = 'guest'
                flash("Selamat datang kembali, " + user[1] + "!", "success")
                return redirect(url_for('guest_dashboard'))  # tukar ke halaman utama tetamu
            else:
                flash("Nama pengguna atau kata laluan salah.", "danger")
        except Exception as e:
            print("Login Error:", e)
            flash("Ralat sistem. Sila cuba lagi.", "danger")
        finally:
            cur.close()

    return render_template('guest_login.html')

# --- Laluan Admin ---
@app.route('/admin/admin_dashboard')
def admin_dashboard():
    print("DEBUG: Session inside /admin_dashboard →", session)
    if 'logged_in' in session and session['role'] == 'admin':
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # 1. Bilangan tetamu
            cur.execute("SELECT COUNT(*) FROM Guest")
            num_guests = cur.fetchone()[0]

            # 2. Tempahan yang belum disahkan
            cur.execute("SELECT COUNT(*) FROM Booking WHERE STATUS = 'Menunggu Pengesahan'")
            num_pending_bookings = cur.fetchone()[0]

            # 3. Bil belum dibayar - COMMENT/REPLACE sebab tiada STATUS dalam Bill
            # cur.execute("SELECT COUNT(*) FROM Bill WHERE STATUS = 'Belum Dibayar'")
            # num_unpaid_bills = cur.fetchone()[0]
            num_unpaid_bills = 0  # atau tambah column baru jika nak guna

            cur.close()

            return render_template('/admin/admin_dashboard.html',
                                   num_guests=num_guests,
                                   num_pending_bookings=num_pending_bookings,
                                   num_unpaid_bills=num_unpaid_bills)

        except Exception as e:
            print("Dashboard Error:", e)
            flash("Ralat ketika mengambil data dari pangkalan data.", "danger")
            return redirect(url_for('index'))

    flash("Sila log masuk sebagai admin untuk mengakses halaman ini.", "warning")
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

@app.route('/admin/admin_bill_management', methods=['GET', 'POST'])
def admin_bill_management():
    print("DEBUG: Session inside /admin/admin_bill_management →", session)

    if 'logged_in' in session and session['role'] == 'admin':
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Kemaskini status bil jika POST
            if request.method == 'POST' and 'bill_id' in request.form:
                bill_id = request.form['bill_id']
                new_status = request.form['status']
                cur.execute("UPDATE BILL SET STATUS = :1 WHERE BILLID = :2", (new_status, bill_id))
                conn.commit()
                flash("Status bil dikemaskini!", "success")

            # Dapatkan filter dari query string
            status_filter = request.args.get('status', 'Semua')
            booking_id_search = request.args.get('booking_id', '')

            # SQL dengan JOIN
            query = """
                SELECT B.BILLID, B.BOOKINGID, B.AMOUNT, B.ISSUEDDATE, B.STATUS, G.FULLNAME
                FROM BILL B
                LEFT JOIN BOOKING BK ON B.BOOKINGID = BK.BOOKINGID
                LEFT JOIN GUEST G ON BK.GUESTID = G.GUESTID
                WHERE 1=1
            """
            params = {}

            if status_filter and status_filter != 'Semua':
                query += " AND B.STATUS = :status"
                params['status'] = status_filter

            if booking_id_search:
                query += " AND B.BOOKINGID = :booking_id"
                params['booking_id'] = booking_id_search

            query += " ORDER BY B.ISSUEDDATE DESC"

            cur.execute(query, params)
            bills = cur.fetchall()

            cur.close()
            conn.close()

            return render_template('admin/admin_bill_management.html',
                                   bills=bills,
                                   selected_status=status_filter,
                                   search_booking_id=booking_id_search)

        except Exception as e:
            flash("Ralat semasa akses bil: " + str(e), "danger")
            return redirect(url_for('admin_dashboard'))

    flash("Sila log masuk sebagai admin.", "warning")
    return redirect(url_for('index'))

@app.route('/admin/kemaskini-tetamu/<int:guest_id>', methods=['GET', 'POST'])
def kemaskini_tetamu(guest_id):
    if 'logged_in' in session and session['role'] == 'admin':
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            if request.method == 'POST':
                fullname = request.form['fullname']
                email = request.form['email']
                phone = request.form['phone']
                username = request.form['username']

                cur.execute("""
                    UPDATE GUEST 
                    SET FULLNAME = :1, EMAIL = :2, PHONE = :3, USERNAME = :4 
                    WHERE GUESTID = :5
                """, (fullname, email, phone, username, guest_id))
                conn.commit()
                flash("Maklumat tetamu dikemaskini!", "success")
                return redirect(url_for('admin_guest_management'))

            # Dapatkan maklumat tetamu untuk pre-fill form
            cur.execute("SELECT FULLNAME, EMAIL, PHONE, USERNAME FROM GUEST WHERE GUESTID = :1", (guest_id,))
            guest = cur.fetchone()

            cur.close()
            conn.close()

            if guest:
                return render_template('kemaskini_tetamu.html', guest=guest, guest_id=guest_id)
            else:
                flash("Tetamu tidak dijumpai.", "warning")
                return redirect(url_for('admin_guest_management'))

        except Exception as e:
            flash("Ralat semasa kemaskini: " + str(e), "danger")
            return redirect(url_for('admin_guest_management'))

    flash("Sila log masuk sebagai admin.", "warning")
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
    print("🚀 Testing Oracle DB Query:")
    query_bookings()
    # use_reloader=False is set to prevent OSError: [WinError 10038] on Windows
    # This means you'll need to manually restart the server after code changes.
    app.run(debug=True, port=5000, use_reloader=False)