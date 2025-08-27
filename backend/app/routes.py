import os
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from fastapi.responses import Response
from app.supabase_client import insert_interest, supabase, update_status


router = APIRouter()

OOP_HANDLES = ["out-of-print-offers", "out-of-print-offers-1"]

class InterestRequest(BaseModel):
    email: str
    product_id: int
    product_title: str
    isbn: str | None = None
    customer_name: str | None = None

class StatusUpdateRequest(BaseModel):
    request_id: str
    new_status: str
    changed_by: str | None = None

@router.api_route("/interest", methods=["POST", "OPTIONS"])
async def create_interest(req: Request):
    try:
        body = await req.json()
        request = InterestRequest(**body)
        result = insert_interest(
            email=request.email,
            product_id=request.product_id,
            product_title=request.product_title,
            isbn=request.isbn,
            customer_name=request.customer_name
        )
        return {"success": True, "data": result}
    except Exception as e:
        print("Error inserting interest:", e)
        raise HTTPException(status_code=500, detail="Failed to record interest.")

@router.get("/interest")
async def get_interest_entries(token: str = "", collection_filter: str | None = None):
    if token != os.getenv("VITE_ADMIN_TOKEN"):
        raise HTTPException(status_code=403, detail="Invalid token")

    try:
        # Base query
        q = supabase.table("product_interest_requests") \
            .select("id, product_id, product_title, email, customer_name, isbn, cr_id, status, cr_seq, created_at, shopify_collection_handles") \
            .order("created_at", desc=True) \
            .limit(100)

        # Normalize and apply collection filter (supports: All | OOP | Frontlist)
        cf = (collection_filter or "All").strip().lower()

        if cf == "oop":
            # Include items overlapping OOP collections OR (no/empty collections AND title starts with "OP: ")
            # Uses PostgREST or() with grouped and() clauses
            q = q.or_(
                "shopify_collection_handles.ov.{out-of-print-offers,out-of-print-offers-1},"
                "and(or(shopify_collection_handles.is.null,shopify_collection_handles.eq.{}),product_title.ilike.OP:%)"
            )

        elif cf == "frontlist":
            # Include items NOT overlapping OOP and NOT starting with "OP: ..."
            # OR (no/empty collections AND NOT starting with "OP: ...")
            q = q.or_(
                "and(shopify_collection_handles.not.ov.{out-of-print-offers,out-of-print-offers-1},product_title.not.ilike.OP:%)",
                "and(or(shopify_collection_handles.is.null,shopify_collection_handles.eq.{}),product_title.not.ilike.OP:%)"
            )
        # else: "all" -> no additional filter

        result = q.execute()
        return {"success": True, "data": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update_status")
async def update_request_status(payload: StatusUpdateRequest, token: str = ""):
    if token != os.getenv("VITE_ADMIN_TOKEN"):
        raise HTTPException(status_code=403, detail="Invalid token")

    try:
        # Debug: incoming payload
        print("📥 Incoming status update payload:", payload.dict())

        # Default to "system" if no changed_by is provided
        actor = payload.changed_by if payload.changed_by else "system"

        # Call the RPC
        result = update_status(
            payload.request_id,
            payload.new_status,
            changed_by=actor,
            source="api",
            optimistic=False
        )

        # Debug: RPC call result
        print("✅ RPC result:", result)

        return {"success": True, "data": result}
    except Exception as e:
        print("❌ Error in update_request_status:", str(e))
        raise HTTPException(status_code=500, detail=str(e))