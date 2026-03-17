from fastapi import APIRouter, HTTPException
import jwt
import os
import time

from app.supabase_client import record_signed_copy_response

router = APIRouter()

SECRET = os.getenv("SIGNED_COPY_TOKEN_SECRET")

VALID = {
    "keep": "keep_order",
    "cancel": "cancel_order",
    "unsigned": "unsigned_copy"
}

@router.post("/signed-copy/respond")
async def respond(payload: dict):
    token = payload.get("token")
    response = payload.get("response")

    if response not in VALID:
        raise HTTPException(400, "Invalid response")

    try:
        decoded = jwt.decode(token, SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(400, "Invalid token")

    row = {
        "token_jti": decoded["jti"],
        "email": decoded["email"],
        "token_email": decoded["email"],

        # product
        "token_product_id": decoded["product_id"],
        "product_id": decoded["product_id"],
        "product_title": decoded.get("product_title"),

        # NEW: deterministic order linkage (from token)
        "order_id": decoded.get("order_id"),
        "order_name": decoded.get("order_name"),
        "line_item_id": decoded.get("line_item_id"),
        "customer_id": decoded.get("customer_id"),

        # response
        "response": VALID[response],

        # metadata
        "raw_token_payload": decoded,
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    if not row.get("order_id") or not row.get("line_item_id"):
        raise HTTPException(400, "Token missing order linkage")

    print(f"[SIGNED COPY] {row['email']} → {row['response']}")

    saved = record_signed_copy_response(row)

    return {"success": True, "id": saved["id"]}