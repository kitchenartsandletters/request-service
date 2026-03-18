#!/usr/bin/env python3
"""
Ingest Signed Copy Orders

- Fetches all Shopify orders (paginated)
- Extracts line items matching TARGET_PRODUCT_ID
- Builds normalized rows
- Deduplicates by line_item_id
- Inserts into Supabase

Supports:
    --dry-run  (no DB writes)
"""

import os
import argparse
import logging
from typing import List, Dict, Any

from dotenv import load_dotenv
from supabase import create_client

# --- ENV SETUP ---
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

SHOP_URL = os.getenv("SHOP_URL")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")

# --- CONFIG ---
TARGET_PRODUCT_ID = "gid://shopify/Product/7179329437829"
TARGET_TITLE = "The Noma Guide to Building Flavour"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger()

# --- CLIENTS ---
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# --- HELPERS ---

def extract_id(gid: str) -> int:
    """Convert Shopify GID to numeric ID"""
    return int(gid.split("/")[-1])


def shopify_graphql(query: str, variables: dict) -> dict:
    import requests
    import time

    url = f"https://{SHOP_URL}/admin/api/2024-01/graphql.json"

    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json",
    }

    while True:
        resp = requests.post(
            url,
            json={"query": query, "variables": variables},
            headers=headers,
        )

        # --- HTTP-level failure ---
        if resp.status_code != 200:
            raise Exception(f"Shopify HTTP error: {resp.text}")

        data = resp.json()

        # --- GraphQL errors ---
        if "errors" in data:
            errors = data["errors"]

            # Handle rate limiting
            if any(
                e.get("extensions", {}).get("code") == "THROTTLED"
                for e in errors
            ):
                log.warning("⚠️ Shopify throttled. Sleeping 2 seconds and retrying...")
                time.sleep(2)
                continue

            # Any other GraphQL error → fail fast
            raise Exception(f"GraphQL errors: {errors}")

        return data["data"]


def build_rows(order: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract matching line items from an order"""
    rows = []

    for edge in order["lineItems"]["edges"]:
        li = edge["node"]
        product = li.get("product")

        if not product:
            continue

        if product["id"] != TARGET_PRODUCT_ID:
            continue

        customer = order.get("customer") or {}

        first_name = (customer.get("firstName") or "").strip() or None
        customer_id = extract_id(customer["id"]) if customer.get("id") else None

        row = {
            "email": order.get("email"),
            "first_name": first_name,
            "customer_first_name": first_name,
            "product_id": extract_id(TARGET_PRODUCT_ID),
            "product_title": TARGET_TITLE,
            "order_id": extract_id(order["id"]),
            "order_name": order["name"],
            "order_number": int(order["name"].replace("#", "")),
            "line_item_id": extract_id(li["id"]),
            "customer_id": (customer_id),
        }

        rows.append(row)

    return rows


def dedupe_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate line_item_id"""
    seen = set()
    deduped = []

    for row in rows:
        lid = row["line_item_id"]
        if lid in seen:
            continue
        seen.add(lid)
        deduped.append(row)

    return deduped


# --- MAIN INGESTION ---

def ingest(dry_run: bool = False):
    log.info("Starting ingestion...")

    query = """
    query ($cursor: String) {
      orders(first: 50, after: $cursor, query: "status:any") {
        pageInfo {
          hasNextPage
          endCursor
        }
        edges {
          node {
            id
            name
            email
            customer {
              id
              firstName
            }
            lineItems(first: 50) {
              edges {
                node {
                  id
                  product {
                    id
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    all_rows = []
    cursor = None
    page = 1

    while True:
        log.info(f"Fetching page {page}...")

        data = shopify_graphql(query, {"cursor": cursor})
        orders = data["orders"]["edges"]

        for edge in orders:
            order = edge["node"]
            rows = build_rows(order)
            all_rows.extend(rows)

        if not data["orders"]["pageInfo"]["hasNextPage"]:
            break

        cursor = data["orders"]["pageInfo"]["endCursor"]
        page += 1

    log.info(f"\nTotal raw matches: {len(all_rows)}")

    deduped = dedupe_rows(all_rows)

    log.info(f"After dedupe: {len(deduped)}")

    # --- VALIDATION SNAPSHOT ---
    missing_email = sum(1 for r in deduped if not r["email"])
    missing_name = sum(1 for r in deduped if not r["first_name"])

    log.info(f"Missing emails: {missing_email}")
    log.info(f"Missing first names: {missing_name}")

    # --- DRY RUN ---
    if dry_run:
        log.info("\n[DRY RUN] Sample rows:")
        for r in deduped[:5]:
            log.info(r)
        return
    
    valid_rows = [r for r in deduped if r["email"]]
    invalid_rows = [r for r in deduped if not r["email"]]

    log.info(f"Valid rows: {len(valid_rows)}")
    log.info(f"Skipped (missing email): {len(invalid_rows)}")

    for r in invalid_rows:
        log.warning(f"Skipping row with missing email: {r['order_name']} (line_item_id={r['line_item_id']})")

    # --- INSERT ---
    if valid_rows:
        log.info("\nInserting into Supabase...")
        supabase.table("signed_copy_campaign_recipients") \
            .insert(valid_rows, upsert=True) \
            .execute()
        log.info(f"Insert complete. Added {len(valid_rows)} rows.")

    log.info("Done.")


# --- ENTRYPOINT ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    ingest(dry_run=args.dry_run)