from dotenv import load_dotenv
import os
import oracledb
from flask import Flask, render_template
app = Flask(__name__)

load_dotenv()  # Load .env

def get_db_connection():
    conn = oracledb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dsn=os.getenv("DB_DSN")
    )
    return conn

@app.route("/bookings")
def show_bookings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM BOOKING")
    bookings = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("bookings.html", bookings=bookings)

# TEST CONNECTION
try:
    conn = get_db_connection()
    print("✅ Connected to Oracle DB")

    # Optional: run a test query
    cursor = conn.cursor()
    cursor.execute("SELECT 'Hello from Oracle DB' FROM dual")
    result = cursor.fetchone()
    print("Result:", result[0])

    conn.close()

except Exception as e:
    print("❌ Connection failed:", e)
