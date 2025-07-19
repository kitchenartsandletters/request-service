import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_interest(email: str, product_id: int, product_title: str):
    response = supabase.table("product_interest_requests").insert({
        "email": email,
        "product_id": product_id,
        "product_title": product_title
    }).execute()

    if not response.data:
        raise Exception("Insert failed or returned no data.")
    
    return response.data

def fetch_all_interest():
    response = supabase.table("product_interest_requests").select("*").execute()
    if not response.data:
        return []
    return response.data
