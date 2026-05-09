import requests
import base64
from datetime import datetime
import os

MPESA_CONSUMER_KEY = os.environ.get("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.environ.get("MPESA_CONSUMER_SECRET")
MPESA_SHORTCODE = os.environ.get("MPESA_SHORTCODE", "174379")
MPESA_PASSKEY = os.environ.get("MPESA_PASSKEY", "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919")
MPESA_CALLBACK_URL = os.environ.get("MPESA_CALLBACK_URL", "https://connect-backend-8x61.onrender.com/donations/mpesa/callback")
MPESA_BASE_URL = "https://sandbox.safaricom.co.ke"

def get_access_token():
    url = f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    credentials = base64.b64encode(
        f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}".encode()
    ).decode()
    response = requests.get(url, headers={"Authorization": f"Basic {credentials}"})
    response.raise_for_status()
    return response.json()["access_token"]

def generate_password():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    raw = f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(raw.encode()).decode()
    return password, timestamp

def stk_push(phone_number: str, amount: int, account_reference: str, description: str):
    try:
        access_token = get_access_token()
        password, timestamp = generate_password()

        phone = str(phone_number).strip()
        if phone.startswith("0"):
            phone = "254" + phone[1:]
        if phone.startswith("+"):
            phone = phone[1:]

        payload = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": MPESA_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": MPESA_CALLBACK_URL,
            "AccountReference": account_reference,
            "TransactionDesc": description
        }

        response = requests.post(
            f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        return response.json()

    except Exception as e:
        print(f"STK Push error: {e}")
        return {"error": str(e)}
