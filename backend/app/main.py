from fastapi import FastAPI
from app.routes import router as interest_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://admin.kitchenartsandletters.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the interest route
app.include_router(interest_router, prefix="/api")
