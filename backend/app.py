import os
import json
import base64
import sqlite3
import requests

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)

# =====================================
# ENVIRONMENT VARIABLES
# =====================================

CONSUMER_KEY = os.getenv("DARAJA_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("DARAJA_CONSUMER_SECRET")
SHORTCODE = os.getenv("MPESA_SHORTCODE", "174379")
PASSKEY = os.getenv("MPESA_PASSKEY")

# IMPORTANT:
# Replace with your publicly accessible callback URL
CALLBACK_URL = os.getenv(
    "MPESA_CALLBACK_URL",
    "https://your-domain.com/mpesa-callback"
)

# =====================================
# DATABASE
# =====================================

DB_NAME = "orders.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        checkout_request_id TEXT,
        merchant_request_id TEXT,
        phone TEXT,
        amount REAL,
        status TEXT,
        result_code TEXT,
        result_desc TEXT,
        mpesa_receipt TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()

# =====================================
# HELPER FUNCTIONS
# =====================================


def validate_phone(phone):
    """
    Converts:
    0712345678
    712345678
    254712345678

    into:
    254712345678
    """

    phone = str(phone).strip()

    if phone.startswith("+254"):
        phone = phone[1:]

    if phone.startswith("07"):
        phone = "254" + phone[1:]

    elif phone.startswith("7"):
        phone = "254" + phone

    return phone


def generate_timestamp():
    return datetime.now().strftime("%Y%m%d%H%M%S")


def generate_password():
    timestamp = generate_timestamp()

    password_string = f"{SHORTCODE}{PASSKEY}{timestamp}"

    encoded_password = base64.b64encode(
        password_string.encode()
    ).decode()

    return encoded_password, timestamp


# =====================================
# OAUTH ACCESS TOKEN
# =====================================

def get_access_token():

    if not CONSUMER_KEY or not CONSUMER_SECRET:
        raise Exception(
            "Missing Daraja credentials in .env"
        )

    url = (
        "https://sandbox.safaricom.co.ke/"
        "oauth/v1/generate?grant_type=client_credentials"
    )

    response = requests.get(
        url,
        auth=(CONSUMER_KEY, CONSUMER_SECRET),
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return data["access_token"]


# =====================================
# STK PUSH
# =====================================

@app.route("/stkpush", methods=["POST"])
def stkpush():

    try:

        data = request.get_json()

        phone = validate_phone(
            data.get("phone")
        )

        amount = float(
            data.get("amount")
        )

        access_token = get_access_token()

        password, timestamp = generate_password()

        headers = {
            "Authorization":
                f"Bearer {access_token}",
            "Content-Type":
                "application/json"
        }

        payload = {
            "BusinessShortCode": SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType":
                "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": CALLBACK_URL,
            "AccountReference":
                "SHOP",
            "TransactionDesc":
                "Shop Payment"
        }

        response = requests.post(
            "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers=headers,
            timeout=30
        )

        result = response.json()

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO orders(
                checkout_request_id,
                merchant_request_id,
                phone,
                amount,
                status,
                created_at
            )
            VALUES(?,?,?,?,?,?)
        """, (
            result.get("CheckoutRequestID"),
            result.get("MerchantRequestID"),
            phone,
            amount,
            "PENDING",
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =====================================
# MPESA CALLBACK
# =====================================

@app.route("/mpesa-callback", methods=["POST"])
def mpesa_callback():

    try:

        callback_data = request.get_json()

        print(
            json.dumps(
                callback_data,
                indent=4
            )
        )

        stk_callback = (
            callback_data["Body"]
            ["stkCallback"]
        )

        result_code = stk_callback["ResultCode"]

        result_desc = stk_callback["ResultDesc"]

        checkout_request_id = (
            stk_callback["CheckoutRequestID"]
        )

        conn = get_db_connection()

        if result_code == 0:

            metadata = (
                stk_callback
                .get("CallbackMetadata", {})
                .get("Item", [])
            )

            receipt = ""

            for item in metadata:

                if item.get("Name") == "MpesaReceiptNumber":
                    receipt = item.get("Value")

            conn.execute("""
                UPDATE orders
                SET
                    status=?,
                    result_code=?,
                    result_desc=?,
                    mpesa_receipt=?
                WHERE checkout_request_id=?
            """, (
                "PAID",
                str(result_code),
                result_desc,
                receipt,
                checkout_request_id
            ))

        else:

            conn.execute("""
                UPDATE orders
                SET
                    status=?,
                    result_code=?,
                    result_desc=?
                WHERE checkout_request_id=?
            """, (
                "FAILED",
                str(result_code),
                result_desc,
                checkout_request_id
            ))

        conn.commit()
        conn.close()

        return jsonify({
            "ResultCode": 0,
            "ResultDesc": "Accepted"
        })

    except Exception as e:

        print("Callback Error:", e)

        return jsonify({
            "ResultCode": 0,
            "ResultDesc": "Received"
        })


# =====================================
# VIEW ORDERS
# =====================================

@app.route("/orders", methods=["GET"])
def get_orders():

    conn = get_db_connection()

    rows = conn.execute("""
        SELECT *
        FROM orders
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in rows
    ])


# =====================================
# CHECK SERVER STATUS
# =====================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "status": "running",
        "service": "Daraja STK Push API"
    })


# =====================================
# START APP
# =====================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )