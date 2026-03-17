import os
import logging
import requests
import base64
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from backend.app.supabase_client import supabase
from utils.token_utils import generate_signed_copy_token
from email_templates.email_templates import build_signed_copy_email

MAILTRAP_URL = "https://send.api.mailtrap.io/api/send"

def send_mailtrap_email(subject, html_body, to_email):
    token = os.getenv("MAILTRAP_API_TOKEN")
    sender = os.getenv("EMAIL_SENDER")

    if sender:
        sender = sender.strip().strip('"').strip("'")

    if not token or not sender:
        raise RuntimeError("Missing MAILTRAP_API_TOKEN or EMAIL_SENDER")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "from": {
            "email": sender,
            "name": "Kitchen Arts & Letters"
        },
        "to": [
            {
                "email": to_email
            }
        ],
        "subject": subject,
        "html": html_body
    }

    res = requests.post(MAILTRAP_URL, headers=headers, json=payload)

    if res.status_code != 200:
        logging.error(res.text)
        raise RuntimeError("Mailtrap send failed")


def run(dry_run=False):
    rows = supabase.table("signed_copy_campaign_recipients") \
        .select("id,email,first_name,product_id,product_title,order_id,order_name,line_item_id,customer_id") \
        .eq("email_sent", False) \
        .execute().data

    print(f"Found {len(rows)} recipients")

    print("SUPABASE URL:", os.getenv("SUPABASE_URL"))

    for row in rows:
        print("ROW BEING USED:", row)
        token = generate_signed_copy_token(row)
        html = build_signed_copy_email(row, token)

        if dry_run:
            print(f"[DRY RUN] Would send to {row['email']}")
            continue

        send_mailtrap_email(
            subject="Quick question about your preorder for The Noma Guide to Building Flavour",
            html_body=html,
            to_email=row["email"]
        )

        supabase.table("signed_copy_campaign_recipients") \
            .update({
                "email_sent": True,
                "email_sent_at": datetime.utcnow().isoformat(),
                "token": token,
                "token_generated_at": datetime.utcnow().isoformat()
            }) \
            .eq("id", row["id"]) \
            .execute()

        print(f"Sent → {row['email']}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    run(dry_run=args.dry_run)