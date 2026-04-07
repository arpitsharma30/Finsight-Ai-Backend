# FinSight AI — Backend

FastAPI backend for FinSight AI, a personal finance and stock tracking platform.

## Tech Stack
- **FastAPI** + Uvicorn
- **yfinance** — live stock price data
- **httpx** — Yahoo Finance search API
- **Groq API** — AI chat (LLaMA 3)
- **Python 3.11+**

## Features
- Global stock search (NSE, BSE, NASDAQ, NYSE, KSE and more)
- Live price + % change via yfinance
- AI financial chat powered by Groq
- Portfolio tracking
- Risk quiz + advisor

## Project Structure


app/
├── routes/
│   ├── stocks.py       # Live stock search + price
│   ├── chat.py         # AI chat via Groq
│   ├── portfolio.py    # Portfolio management
│   ├── quiz.py         # Risk assessment quiz
│   ├── auth_routes.py  # Authentication
│   └── user_routes.py  # User profile
├── main.py             # FastAPI app entry point
├── auth.py             # Auth logic
├── db.py               # Database connection
├── advisor.py          # Financial advisor logic
└── security.py         # JWT / security utils
## Setup
```bash
# Clone
git clone https://github.com/arpitsharma30/Finsight-Ai-Backend.git
cd Finsight-Ai-Backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Add environment variables
cp .env.example .env
# Fill in GROQ_API_KEY and other vars

# Run
uvicorn app.main:app --reload
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/stocks?symbol=nvidia` | Search any stock globally |
| POST | `/chat` | AI financial chat |
| GET | `/portfolio` | Get user portfolio |
| POST | `/quiz` | Submit risk quiz |

## Deployment
Deployed on AWS EC2 (t2.micro) with Nginx reverse proxy.

## Frontend
[Finsight--Ai](https://github.com/arpitsharma30/Finsight--Ai)
