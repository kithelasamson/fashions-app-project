import os
import json
import base64
import sqlite3
import requests

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()


app = Flask(__name__)

# Allow Android/Kivy app requests
CORS(app)


# ==================================================
# ENVIRONMENT VARIABLES
# ==================================================

CONSUMER_KEY = os.getenv(
    "DARAJA_CONSUMER_KEY"
)

CONSUMER_SECRET = os.getenv(
    "DARAJA_CONSUMER_SECRET"
)


SHORTCODE = os.getenv(
    "MPESA_SHORTCODE",
    "174379"
)


PASSKEY = os.getenv(
    "MPESA_PASSKEY"
)


CALLBACK_URL = os.getenv(
    "MPESA_CALLBACK_URL"
)


DARAJA_ENV = os.getenv(
    "DARAJA_ENV",
    "sandbox"
)



if DARAJA_ENV == "production":

    MPESA_BASE_URL = (
        "https://api.safaricom.co.ke"
    )

else:

    MPESA_BASE_URL = (
        "https://sandbox.safaricom.co.ke"
    )



# ==================================================
# DATABASE
# ==================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


DB_NAME = os.path.join(
    BASE_DIR,
    "orders.db"
)



def get_db_connection():

    conn = sqlite3.connect(
        DB_NAME
    )

    conn.row_factory = sqlite3.Row

    return conn



def init_db():

    conn = get_db_connection()


    conn.execute("""
    CREATE TABLE IF NOT EXISTS orders(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        checkout_request_id TEXT UNIQUE,

        merchant_request_id TEXT,

        phone TEXT,

        amount REAL,

        status TEXT,

        result_code TEXT,

        result_desc TEXT,

        mpesa_receipt TEXT,

        transaction_date TEXT,

        amount_paid REAL,

        paid_phone TEXT,

        created_at TEXT

    )
    """)


    conn.commit()

    conn.close()



init_db()



# ==================================================
# HELPERS
# ==================================================


def validate_phone(phone):

    if not phone:

        raise ValueError(
            "Phone number required"
        )


    phone = str(phone).strip()



    if phone.startswith("+254"):

        phone = phone[1:]



    elif phone.startswith("07"):

        phone = (
            "254"
            + phone[1:]
        )



    elif phone.startswith("7"):

        phone = (
            "254"
            + phone
        )



    if len(phone) != 12:

        raise ValueError(
            "Use format 2547XXXXXXXX"
        )


    return phone




def timestamp():

    return datetime.now().strftime(
        "%Y%m%d%H%M%S"
    )




def generate_password():

    time = timestamp()


    data = (
        f"{SHORTCODE}"
        f"{PASSKEY}"
        f"{time}"
    )


    password = base64.b64encode(
        data.encode()
    ).decode()


    return password,time




def get_access_token():

    if not CONSUMER_KEY:

        raise Exception(
            "Missing DARAJA_CONSUMER_KEY"
        )


    url = (
        f"{MPESA_BASE_URL}"
        "/oauth/v1/generate"
        "?grant_type=client_credentials"
    )



    response = requests.get(

        url,

        auth=(

            CONSUMER_KEY,

            CONSUMER_SECRET

        ),

        timeout=30

    )


    response.raise_for_status()


    return response.json()["access_token"]





# ==================================================
# ROUTES
# ==================================================



@app.route("/")
def home():

    return jsonify({

        "service":
        "Fashion Store Payment API",

        "status":
        "running",

        "time":
        datetime.now().isoformat()

    })




@app.route("/api/test")
def test():

    return jsonify({

        "message":
        "Kivy app connected successfully"

    })





# ==================================================
# STK PUSH
# ==================================================


@app.route(
    "/stkpush",
    methods=["POST"]
)
def stkpush():


    try:


        data = request.get_json()



        phone = validate_phone(

            data.get("phone")

        )


        amount = float(

            data.get(
                "amount"
            )

        )



        token = get_access_token()



        password, time = generate_password()



        headers = {


            "Authorization":

            f"Bearer {token}",


            "Content-Type":

            "application/json"

        }




        payload = {


            "BusinessShortCode":

            SHORTCODE,


            "Password":

            password,


            "Timestamp":

            time,


            "TransactionType":

            "CustomerPayBillOnline",


            "Amount":

            int(amount),


            "PartyA":

            phone,


            "PartyB":

            SHORTCODE,


            "PhoneNumber":

            phone,


            "CallBackURL":

            CALLBACK_URL,


            "AccountReference":

            "FashionStore",


            "TransactionDesc":

            "Payment"

        }




        response = requests.post(


            MPESA_BASE_URL +

            "/mpesa/stkpush/v1/processrequest",


            json=payload,


            headers=headers,


            timeout=30

        )



        result = response.json()



        checkout = result.get(

            "CheckoutRequestID"

        )



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

        """,

        (

        checkout,

        result.get(
            "MerchantRequestID"
        ),

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

            "error":

            str(e)

        }),500





# ==================================================
# CALLBACK
# ==================================================


@app.route(
    "/mpesa-callback",
    methods=["POST"]
)

def callback():

    data = request.json


    print(
        json.dumps(
            data,
            indent=4
        )
    )


    return jsonify({

        "ResultCode":0,

        "ResultDesc":
        "Accepted"

    })





# ==================================================
# ORDERS
# ==================================================


@app.route("/orders")
def orders():


    conn = get_db_connection()


    rows = conn.execute(

        "SELECT * FROM orders ORDER BY id DESC"

    ).fetchall()


    conn.close()


    return jsonify([

        dict(x)

        for x in rows

    ])





# ==================================================
# RENDER START
# ==================================================


if __name__ == "__main__":


    app.run(

        host="0.0.0.0",

        port=5000

    )