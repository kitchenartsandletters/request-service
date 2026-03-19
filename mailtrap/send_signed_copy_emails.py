import os
import time
import logging
import requests
from datetime import datetime
from typing import List

from dotenv import load_dotenv
load_dotenv()

from backend.app.supabase_client import supabase
from utils.token_utils import generate_signed_copy_token
from email_templates.email_templates import build_signed_copy_email

MAILTRAP_URL = "https://send.api.mailtrap.io/api/send"

logging.basicConfig(level=logging.INFO)


# ---------------------------
# CONFIG (CLI OVERRIDES BELOW)
# ---------------------------
DEFAULT_BATCH_SIZE = 25
DEFAULT_SLEEP_SECONDS = 0.4
MAX_RETRIES = 3


# ---------------------------
# MAIL SEND
# ---------------------------
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
        "to": [{"email": to_email}],
        "subject": subject,
        "html": html_body
    }

    res = requests.post(MAILTRAP_URL, headers=headers, json=payload)

    if res.status_code not in (200, 202):
        raise RuntimeError(f"Mailtrap failed: {res.text}")


# ---------------------------
# RETRY WRAPPER
# ---------------------------
def with_retry(fn, max_retries=MAX_RETRIES, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            sleep_time = base_delay * (2 ** attempt)
            logging.warning(f"Retrying in {sleep_time}s → {e}")
            time.sleep(sleep_time)


# ---------------------------
# PROCESS SINGLE ROW
# ---------------------------
def process_row(row, dry_run=False):
    email = row["email"]

    token = generate_signed_copy_token(row)
    html = build_signed_copy_email(row, token)

    if dry_run:
        logging.info(f"[DRY RUN] Would send to {email}")
        return "dry_run"

    # 1️⃣ SEND EMAIL (with retry)
    with_retry(lambda: send_mailtrap_email(
        subject="Quick question about your preorder for The Noma Guide to Building Flavour",
        html_body=html,
        to_email=email
    ))

    now = datetime.utcnow().isoformat()

    # 2️⃣ UPDATE RECIPIENT (safe conditional update)
    def update_recipient():
        return supabase.table("signed_copy_campaign_recipients") \
            .update({
                "email_sent": True,
                "email_sent_at": now,
                "token": token,
                "token_generated_at": now
            }) \
            .eq("id", row["id"]) \
            .eq("email_sent", False) \
            .execute()

    with_retry(update_recipient)

    # 3️⃣ LOG SUCCESS
    def log_success():
        return supabase.table("email_log").insert({
            "request_id": row["id"],
            "email": email,
            "status": "sent",
            "sent_at": now
        }).execute()

    with_retry(log_success)

    logging.info(f"Sent → {email}")
    return "sent"


# ---------------------------
# MAIN RUNNER
# ---------------------------
def run(dry_run=False, batch_size=DEFAULT_BATCH_SIZE, sleep_seconds=DEFAULT_SLEEP_SECONDS, limit=None, randomize=False, exclude_emails=None):
    rows = supabase.table("signed_copy_campaign_recipients") \
        .select("id,email,first_name,product_id,product_title,order_id,order_name,line_item_id,customer_id") \
        .eq("email_sent", False) \
        .execute().data

    # --- OPTIONAL EXCLUSIONS ---
    if exclude_emails:
        exclude_set = set(e.strip().lower() for e in exclude_emails)
        rows = [r for r in rows if r["email"].lower() not in exclude_set]

    # --- OPTIONAL RANDOMIZATION ---
    if randomize:
        import random
        random.shuffle(rows)

    # --- OPTIONAL LIMIT ---
    if limit:
        rows = rows[:limit]

    total = len(rows)
    logging.info(f"Found {total} recipients")

    if not rows:
        logging.info("No recipients to send.")
        return

    success_count = 0
    failure_queue: List[dict] = []

    # ---------------------------
    # BATCH LOOP
    # ---------------------------
    for i in range(0, total, batch_size):
        batch = rows[i:i + batch_size]
        logging.info(f"\n--- Processing batch {i//batch_size + 1} ({len(batch)} rows) ---")

        for row in batch:
            try:
                result = process_row(row, dry_run=dry_run)
                if result == "sent":
                    success_count += 1

            except Exception as e:
                error_msg = str(e)
                logging.error(f"FAILED → {row['email']} → {error_msg}")

                failure_queue.append(row)

                # failure log (non-blocking)
                try:
                    supabase.table("email_log").insert({
                        "request_id": row["id"],
                        "email": row["email"],
                        "status": "failed",
                        "error": error_msg,
                        "sent_at": datetime.utcnow().isoformat()
                    }).execute()
                except Exception as log_err:
                    logging.error(f"Failed to log error: {log_err}")

            # rate limit
            time.sleep(sleep_seconds)

    # ---------------------------
    # RETRY FAILED
    # ---------------------------
    if failure_queue:
        logging.info(f"\n--- RETRYING {len(failure_queue)} FAILED ROWS ---")

        for row in failure_queue:
            try:
                process_row(row, dry_run=dry_run)
                success_count += 1
            except Exception as e:
                logging.error(f"FINAL FAIL → {row['email']} → {e}")

    # ---------------------------
    # SUMMARY
    # ---------------------------
    logging.info("\n--- RUN COMPLETE ---")
    logging.info(f"Total: {total}")
    if dry_run:
        logging.info(f"Dry run processed: {total}")
    else:
        logging.info(f"Success: {success_count}")
        logging.info(f"Failed: {total - success_count}")


# ---------------------------
# CLI
# ---------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--sleep", type=float, default=DEFAULT_SLEEP_SECONDS)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--randomize", action="store_true")
    parser.add_argument("--exclude", type=str, default=None, help="Comma-separated emails to exclude")

    args = parser.parse_args()

    exclude_emails = args.exclude.split(",") if args.exclude else None

    run(
        dry_run=args.dry_run,
        batch_size=args.batch_size,
        sleep_seconds=args.sleep,
        limit=args.limit,
        randomize=args.randomize,
        exclude_emails=exclude_emails
    )