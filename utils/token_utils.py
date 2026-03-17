import os
import time
import uuid
import jwt

SIGNED_COPY_TOKEN_SECRET = os.getenv("SIGNED_COPY_TOKEN_SECRET")
SIGNED_COPY_TOKEN_ALG = "HS256"

def generate_signed_copy_token(row: dict) -> str:
    now = int(time.time())

    payload = {
        "jti": str(uuid.uuid4()),
        "email": row["email"].strip().lower(),
        "first_name": row.get("first_name"),
        "product_id": row.get("product_id"),
        "product_title": row.get("product_title"),
        "order_id": row.get("order_id"),
        "order_name": row.get("order_name"),
        "line_item_id": row.get("line_item_id"),
        "customer_id": row.get("customer_id"),
        "campaign_key": "noma-signed-copy-decision",
        "iat": now,
        "exp": now + (60 * 60 * 24 * 30),
    }

    return jwt.encode(payload, SIGNED_COPY_TOKEN_SECRET, algorithm=SIGNED_COPY_TOKEN_ALG)