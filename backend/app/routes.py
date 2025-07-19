import os
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from app.supabase_client import insert_interest, supabase

router = APIRouter()

class InterestRequest(BaseModel):
    email: str
    product_id: int
    product_title: str

@router.post("/api/interest")
async def create_interest(request: InterestRequest):
    try:
        result = insert_interest(
            email=request.email,
            product_id=request.product_id,
            product_title=request.product_title
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/interest")
async def get_interest_entries(token: str = ""):
    if token != os.getenv("VITE_ADMIN_TOKEN"):
        raise HTTPException(status_code=403, detail="Invalid token")

    try:
        result = supabase.table("product_interest_requests").select("*").order("created_at", desc=True).limit(100).execute()
        return {"success": True, "data": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
