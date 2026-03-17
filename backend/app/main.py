from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router as interest_router
from app.signed_copy_routes import router as signed_copy_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://admin.kitchenartsandletters.com",
        "https://www.kitchenartsandletters.com",
        "https://kitchenartsandletters.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interest_router, prefix="/api")
app.include_router(signed_copy_router, prefix="/api")