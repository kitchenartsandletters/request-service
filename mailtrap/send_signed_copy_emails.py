import os
import logging
import requests
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

    if res.status_code not in (200, 202):
        logging.error(res.text)
        raise RuntimeError("Mailtrap send failed")


def run(dry_run=False):
    rows = supabase.table("signed_copy_campaign_recipients") \
        .select("id,email,first_name,product_id,product_title,order_id,order_name,line_item_id,customer_id") \
        .eq("email_sent", False) \
        .execute().data

    print(f"Found {len(rows)} recipients")

    if not rows:
        print("No recipients to send.")
        return

    print("SUPABASE URL:", os.getenv("SUPABASE_URL"))

    for row in rows:
        print("ROW BEING USED:", row)

        try:
            token = generate_signed_copy_token(row)
            html = build_signed_copy_email(row, token)

            if dry_run:
                print(f"[DRY RUN] Would send to {row['email']}")
                continue

            # 1️⃣ SEND EMAIL FIRST
            send_mailtrap_email(
                subject="Quick question about your preorder for The Noma Guide to Building Flavour",
                html_body=html,
                to_email=row["email"]
            )

            now = datetime.utcnow().isoformat()

            # 2️⃣ UPDATE RECIPIENT (separate failure boundary)
            supabase.table("signed_copy_campaign_recipients") \
                .update({
                    "email_sent": True,
                    "email_sent_at": now,
                    "token": token,
                    "token_generated_at": now
                }) \
                .eq("id", row["id"]).eq("email_sent", False) \
                .execute()

            # 3️⃣ LOG SUCCESS
            supabase.table("email_log").insert({
                "request_id": row["id"],
                "email": row["email"],
                "status": "sent",
                "sent_at": now
            }).execute()

            print(f"Sent → {row['email']}")

        except Exception as e:
            error_msg = str(e)
            logging.error(f"FAILED → {row['email']} → {error_msg}")

            # ❌ failure log
            supabase.table("email_log").insert({
                "request_id": row["id"],
                "email": row["email"],
                "status": "failed",
                "error": error_msg,
                "sent_at": datetime.utcnow().isoformat()
            }).execute()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    run(dry_run=args.dry_run)