from app.supabase_client import shopify_graphql

email = "letters@kitchenartsandletters.com"
product_id = 7179329437829

query = """
query ($query: String!) {
  orders(first: 5, query: $query, reverse: true) {
    edges {
      node {
        id
        name
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
  }
}
"""

data = shopify_graphql(query, {"query": f"email:{email} AND status:any"})

print("RAW DATA:", data)

for edge in data["orders"]["edges"]:
    order = edge["node"]
    print("\nORDER:", order["name"])
    
    for li_edge in order["lineItems"]["edges"]:
        li = li_edge["node"]
        product = li.get("product")

        if product:
            print("  Product:", product["id"])
            print("  LineItem:", li["id"])

        if product and str(product_id) in product["id"]:
            print("  ✅ MATCH FOUND")
            print("  👉 Use this line_item_id:")
            print("     ", int(li["id"].split("/")[-1]))
