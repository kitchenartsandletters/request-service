from fastapi import FastAPI
from app.routes import router as interest_router

app = FastAPI()

# Mount the interest route
app.include_router(interest_router, prefix="/api")
