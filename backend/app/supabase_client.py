import os
import requests
from typing import Any, Dict

from supabase import create_client, Client

SHOP_URL = os.getenv("SHOP_URL")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-10")

SIGNED_COPY_PRODUCT_ID = 7179329437829

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Missing Supabase credentials")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

    inserted = supabase.table("signed_copy_responses") \
        .insert(row) \
        .execute()

    if not inserted.data:
        raise Exception("Failed to insert signed_copy_responses row")

    return inserted.data[0]

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