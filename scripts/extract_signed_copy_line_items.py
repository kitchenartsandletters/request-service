import os
import requests
from dotenv import load_dotenv
load_dotenv()

SHOP_URL = os.getenv("SHOP_URL")
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")

if not SHOP_URL or not ACCESS_TOKEN:
    raise ValueError("Missing SHOP_URL or SHOPIFY_ACCESS_TOKEN. Make sure your .env is loaded.")

API_URL = f"https://{SHOP_URL}/admin/api/2024-01/graphql.json"

def fetch_order(order_id):
    query = """
    query ($id: ID!) {
      order(id: $id) {
        name
        email
        customer { 
          id
          firstName 
        }
        lineItems(first: 20) {
          edges {
            node {
              id
              title
              product {
                id
              }
            }
          }
        }
      }
    }
    """

    gid = f"gid://shopify/Order/{order_id}"

    res = requests.post(
        API_URL,
        headers={
            "X-Shopify-Access-Token": ACCESS_TOKEN,
            "Content-Type": "application/json"
        },
        json={"query": query, "variables": {"id": gid}}
    )

    return res.json()["data"]["order"]


def extract(order_id, target_product_id):
    order = fetch_order(order_id)

    for edge in order["lineItems"]["edges"]:
        node = edge["node"]

        product_gid = node["product"]["id"]
        product_id = int(product_gid.split("/")[-1])

        if product_id == target_product_id:
            return {
                "email": order["email"],
                "customer_first_name": order["customer"]["firstName"],
                "order_id": order_id,
                "order_name": order["name"],
                "customer_id": int(order["customer"]["id"].split("/")[-1]),
                "line_item_id": int(node["id"].split("/")[-1]),
                "product_id": product_id,
                "product_title": node["title"]
            }

    return None


if __name__ == "__main__":
    import sys

    order_id = int(sys.argv[1])
    PRODUCT_ID = 7179329437829

    result = extract(order_id, PRODUCT_ID)

    if result:
        print(result)
    else:
        print("No matching line item found")