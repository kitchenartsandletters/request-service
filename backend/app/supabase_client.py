import os
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid
import requests
from typing import Any, Dict

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Shopify env
SHOP_URL = os.getenv("SHOP_URL")  # e.g. castironbooks.myshopify.com
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-10")

SIGNED_COPY_PRODUCT_ID = 7179329437829

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def _normalize_tags(tag_str: str | None):
    if not tag_str:
        return None
    tags = [t.strip() for t in tag_str.split(",")]
    tags = [t for t in tags if t]
    return tags or None

def _enrich_from_shopify(product_id: int):
    """
    Best-effort fetch of tags + collections (titles + handles).
    Returns a dict suitable to merge into the insert payload.
    """
    if not SHOP_URL or not SHOPIFY_ACCESS_TOKEN:
        return {}

    session = requests.Session()
    session.headers.update({"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN})
    base = f"https://{SHOP_URL}/admin/api/{SHOPIFY_API_VERSION}"

    try:
        pr = session.get(f"{base}/products/{product_id}.json", timeout=12)
        pr.raise_for_status()
        product = pr.json().get("product", {})
        tags = _normalize_tags(product.get("tags"))

        cr = session.get(f"{base}/collects.json",
                         params={"product_id": product_id, "limit": 250},
                         timeout=12)
        cr.raise_for_status()
        coll_ids = [c["collection_id"] for c in cr.json().get("collects", [])]

        titles: list[str] = []
        handles: list[str] = []
        for cid in coll_ids:
            r = session.get(f"{base}/collections/{cid}.json", timeout=10)
            if r.status_code == 200:
                coll = r.json().get("collection", {}) or {}
                title = coll.get("title")
                handle = coll.get("handle")
                if title:
                    titles.append(title)
                if handle:
                    handles.append(handle)

        out = {}
        if tags is not None:
            out["product_tags"] = tags
        if titles:
            out["shopify_collections"] = titles
        if handles:
            out["shopify_collection_handles"] = handles
        return out

    except Exception as e:
        print("Enrichment failed (non-fatal):", e)
        return {}

def insert_interest(email: str, product_id: int, product_title: str, isbn: str = None, customer_name: str = None):
    cr_id = f"CR{uuid.uuid4().hex[:8].upper()}"

    if not customer_name or not customer_name.strip():
        customer_name = None
    else:
        customer_name = customer_name.strip()

    payload = {
        "email": email,
        "product_id": product_id,
        "product_title": product_title,
        "isbn": isbn,
        "cr_id": cr_id,
        "customer_name": customer_name
    }

    enrich = _enrich_from_shopify(product_id)
    if enrich:
        payload.update(enrich)

    response = supabase.table("product_interest_requests").insert(payload).execute()

    if not response.data:
        raise Exception("Insert failed or returned no data.")
    
    return response.data

def fetch_all_interest():
    response = supabase.table("product_interest_requests") \
        .select("id, product_id, product_title, email, customer_name, isbn, cr_id, status, cr_seq, created_at") \
        .execute()
    if not response.data:
        return []
    return response.data

def update_status(request_id: str, new_status: str, changed_by: str = "system", source: str = "api", optimistic: bool = False):
    print("📤 Calling RPC update_status_with_log with params:", {
        "req_id": request_id,
        "new_stat": new_status,
        "actor": changed_by,
        "src": source,
        "is_optimistic": optimistic
    })

    resp = supabase.rpc(
        "update_status_with_log",
        {
            "req_id": request_id,
            "new_stat": new_status,
            "actor": changed_by,
            "src": source,
            "is_optimistic": optimistic
        }
    ).execute()

    print("📥 Raw Supabase RPC response:", resp)

    if getattr(resp, "error", None):
        print("❌ Supabase RPC error:", resp.error)
        raise Exception(f"Status update failed: {resp.error}")
    
    return {"success": True}


# --- NEW SIGNED COPY HELPERS (APPENDED ONLY) ---

def shopify_graphql(query: str, variables: dict | None = None) -> dict:
    if not SHOP_URL or not SHOPIFY_ACCESS_TOKEN:
        raise Exception("Missing Shopify credentials")

    url = f"https://{SHOP_URL}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json",
    }

    r = requests.post(
        url,
        headers=headers,
        json={"query": query, "variables": variables or {}},
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()

    if data.get("errors"):
        raise Exception(f"Shopify GraphQL errors: {data['errors']}")

    return data["data"]

def record_signed_copy_response(row: Dict[str, Any]) -> Dict[str, Any]:
    existing = supabase.table("signed_copy_responses") \
        .select("*") \
        .eq("token_jti", row["token_jti"]) \
        .limit(1) \
        .execute()

    if existing.data:
        return existing.data[0]

    try:
        inserted = supabase.table("signed_copy_responses") \
            .insert(row) \
            .execute()

        if not inserted.data:
            raise Exception("Failed to insert signed_copy_responses row")

        return inserted.data[0]

    except Exception:
        # If insert failed (likely due to unique constraint),
        # fetch the existing row instead of crashing
        retry = supabase.table("signed_copy_responses") \
            .select("*") \
            .eq("token_jti", row["token_jti"]) \
            .limit(1) \
            .execute()

        if retry.data:
            return retry.data[0]

        raise

def enrich_signed_copy_response(saved_row: Dict[str, Any]) -> Dict[str, Any]:
    email = saved_row["email"]
    product_id = saved_row["product_id"]

    query = """
    query FindOrdersForSignedCopyDecision($query: String!) {
      orders(first: 10, query: $query, reverse: true) {
        edges {
          node {
            id
            name
            orderNumber
            note
            customer {
              id
              firstName
              lastName
              email
            }
            lineItems(first: 50) {
              edges {
                node {
                  id
                  title
                  quantity
                  variant {
                    id
                  }
                  product {
                    id
                    title
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    search_query = f'email:{email} AND status:any'
    data = shopify_graphql(query, {"query": search_query})

    matched = None
    enrichment = {"candidate_orders": []}

    for edge in data["orders"]["edges"]:
        order = edge["node"]
        order_gid = order["id"]
        order_id_numeric = int(order_gid.split("/")[-1])

        line_edges = order["lineItems"]["edges"]
        for le in line_edges:
            li = le["node"]
            product = li.get("product")
            if not product:
                continue

            try:
                line_product_id = int(product["id"].split("/")[-1])
            except Exception:
                continue

            if line_product_id == product_id:
                matched = {
                    "order_id": order_id_numeric,
                    "order_name": order["name"],
                    "order_number": order["orderNumber"],
                    "line_item_id": int(li["id"].split("/")[-1]),
                    "line_item_title": li["title"],
                    "product_title": product.get("title"),
                    "customer_id": int(order["customer"]["id"].split("/")[-1]) if order.get("customer") and order["customer"].get("id") else None,
                    "customer_first_name": order["customer"]["firstName"] if order.get("customer") else None,
                    "customer_last_name": order["customer"]["lastName"] if order.get("customer") else None,
                    "enrichment": {
                        "matched_via": "email + product_id",
                        "shopify_order_gid": order_gid,
                    },
                    "status": "recorded",
                }
                break

        enrichment["candidate_orders"].append({
            "order_name": order["name"],
            "order_id": order_id_numeric,
        })

        if matched:
            break

    if not matched:
        matched = {
            "status": "needs_review",
            "enrichment": {
                "matched_via": "email_only_no_product_match",
                **enrichment
            }
        }

    updated = supabase.table("signed_copy_responses") \
        .update(matched) \
        .eq("id", saved_row["id"]) \
        .execute()

    if not updated.data:
        raise Exception("Failed to update signed copy response enrichment")

    return updated.data[0]