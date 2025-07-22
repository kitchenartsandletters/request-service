import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def generate_next_cr_id():
    response = supabase.table("product_interest_requests").select("cr_id").order("created_at", desc=True).limit(1).execute()
    if not response.data:
        next_id = 1
    else:
        latest = response.data[0]["cr_id"]
        try:
            number = int(latest.replace("CR", ""))
            next_id = number + 1
        except:
            next_id = 1
    return f"CR{next_id:05d}"

def insert_interest(email: str, product_id: int, product_title: str, isbn: str):
    response = supabase.table("product_interest_requests").insert({
        "email": email,
        "product_id": product_id,
        "product_title": product_title,
        "isbn": isbn,
        "cr_id": generate_next_cr_id()
    }).execute()

    if not response.data:
        raise Exception("Insert failed or returned no data.")
    
    return response.data

def fetch_all_interest():
    response = supabase.table("product_interest_requests").select("*").execute()
    if not response.data:
        return []
    return response.data
