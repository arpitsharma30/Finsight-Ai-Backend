from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routes import quiz, stocks, chat, portfolio, auth_routes, user_routes
from app.db import init_db

load_dotenv()

app = FastAPI(title="FinSight AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(quiz.router)
app.include_router(stocks.router)
app.include_router(chat.router)
app.include_router(portfolio.router)
app.include_router(auth_routes.router)
app.include_router(user_routes.router)


@app.on_event("startup")
def startup_init_db():
    init_db()