from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import yfinance as yf
from app.auth import require_user
from app.db import get_conn
from app.security import utc_now_iso
from app.advisor import classify_risk, recommendation_text


router = APIRouter(prefix="/user", tags=["user"])


class ProfileBody(BaseModel):
    age: int
    monthly_savings: int
    income: int
    loss_reaction: int
    goal: str = "Long-term wealth"
    horizon: str = "5+ years"
    experience: str = "Beginner"


class GoalBody(BaseModel):
    title: str
    target_amount: float
    target_date: str
    monthly_contribution: float


class TxnBody(BaseModel):
    symbol: str
    name: str
    qty: float
    buy_price: float
    exchange: str = "NSE"


def _market_price(symbol: str, fallback: float) -> float:
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        return round(float(ticker.fast_info.last_price), 2)
    except Exception:
        return round(float(fallback), 2)


@router.post("/profile")
async def upsert_profile(body: ProfileBody, user=Depends(require_user)):
    risk_level, _score = classify_risk(body.age, body.monthly_savings, body.loss_reaction)
    advice, ai_advice = recommendation_text(risk_level, body.goal)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO profiles(
            user_id, age, monthly_savings, income, loss_reaction, goal, horizon, experience,
            risk_level, advice, ai_advice, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            age=excluded.age,
            monthly_savings=excluded.monthly_savings,
            income=excluded.income,
            loss_reaction=excluded.loss_reaction,
            goal=excluded.goal,
            horizon=excluded.horizon,
            experience=excluded.experience,
            risk_level=excluded.risk_level,
            advice=excluded.advice,
            ai_advice=excluded.ai_advice,
            updated_at=excluded.updated_at
        """,
        (
            user["id"], body.age, body.monthly_savings, body.income, body.loss_reaction, body.goal, body.horizon, body.experience,
            risk_level, advice, ai_advice, utc_now_iso(),
        ),
    )
    conn.commit()
    conn.close()
    return {
        "risk_level": risk_level,
        "advice": advice,
        "ai_advice": ai_advice,
        "compliance_note": "Educational guidance only, not guaranteed returns or personalized regulated advice.",
    }


@router.get("/profile")
async def get_profile(user=Depends(require_user)):
    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM profiles WHERE user_id = ?", (user["id"],)).fetchone()
    conn.close()
    if not row:
        return {"profile": None}
    return {"profile": dict(row)}


@router.post("/goals")
async def add_goal(body: GoalBody, user=Depends(require_user)):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO goals(user_id, title, target_amount, target_date, monthly_contribution, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'active', ?)
        """,
        (user["id"], body.title, body.target_amount, body.target_date, body.monthly_contribution, utc_now_iso()),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/goals")
async def list_goals(user=Depends(require_user)):
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM goals WHERE user_id = ? ORDER BY id DESC", (user["id"],)).fetchall()
    conn.close()
    return {"goals": [dict(r) for r in rows]}


@router.post("/transactions")
async def add_transaction(body: TxnBody, user=Depends(require_user)):
    if body.qty <= 0 or body.buy_price <= 0:
        raise HTTPException(status_code=400, detail="qty and buy_price must be > 0")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO transactions(user_id, symbol, name, qty, buy_price, exchange, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user["id"], body.symbol.upper(), body.name, body.qty, body.buy_price, body.exchange, utc_now_iso()),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/transactions")
async def list_transactions(user=Depends(require_user)):
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY id DESC", (user["id"],)).fetchall()
    conn.close()
    return {"transactions": [dict(r) for r in rows]}


@router.delete("/transactions/{txn_id}")
async def delete_transaction(txn_id: int, user=Depends(require_user)):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (txn_id, user["id"]))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/portfolio")
async def user_portfolio(user=Depends(require_user)):
    conn = get_conn()
    cur = conn.cursor()
    txns = cur.execute("SELECT * FROM transactions WHERE user_id = ?", (user["id"],)).fetchall()
    profile = cur.execute("SELECT risk_level, ai_advice FROM profiles WHERE user_id = ?", (user["id"],)).fetchone()
    conn.close()

    grouped = defaultdict(lambda: {"qty": 0.0, "cost_total": 0.0, "name": "", "exchange": "NSE"})
    for t in txns:
        g = grouped[t["symbol"]]
        g["qty"] += float(t["qty"])
        g["cost_total"] += float(t["qty"]) * float(t["buy_price"])
        g["name"] = t["name"]
        g["exchange"] = t["exchange"]

    holdings = []
    total_value = 0.0
    total_cost = 0.0
    for sym, g in grouped.items():
        if g["qty"] <= 0:
            continue
        buy_price = round(g["cost_total"] / g["qty"], 2)
        current_price = _market_price(sym, buy_price)
        value = round(current_price * g["qty"], 2)
        cost = round(buy_price * g["qty"], 2)
        total_value += value
        total_cost += cost
        gain_pct = round(((current_price - buy_price) / buy_price) * 100, 2) if buy_price else 0
        holdings.append(
            {
                "symbol": sym,
                "name": g["name"] or sym,
                "qty": round(g["qty"], 4),
                "buy_price": buy_price,
                "current_price": current_price,
                "value": value,
                "gain_pct": gain_pct,
                "exchange": g["exchange"],
            }
        )

    holdings.sort(key=lambda x: x["value"], reverse=True)
    for h in holdings:
        h["allocation"] = round((h["value"] / total_value) * 100, 2) if total_value else 0

    total_gain = round(total_value - total_cost, 2)
    gain_pct = round(((total_value - total_cost) / total_cost) * 100, 2) if total_cost else 0

    return {
        "risk_level": profile["risk_level"] if profile else "Unknown",
        "total_value": round(total_value, 2),
        "total_gain": total_gain,
        "gain_pct": gain_pct,
        "holdings": holdings,
        "ai_tip": profile["ai_advice"] if profile else "Add your profile to receive personalized guidance.",
        "compliance_note": "Educational guidance only. Markets involve risk; review suitability before investing.",
    }


@router.get("/dashboard")
async def user_dashboard(user=Depends(require_user)):
    portfolio = await user_portfolio(user)
    conn = get_conn()
    cur = conn.cursor()
    profile = cur.execute("SELECT * FROM profiles WHERE user_id = ?", (user["id"],)).fetchone()
    goals = cur.execute("SELECT * FROM goals WHERE user_id = ? AND status = 'active'", (user["id"],)).fetchall()
    conn.close()

    goal_target = sum(float(g["target_amount"]) for g in goals) if goals else 0
    goal_monthly = sum(float(g["monthly_contribution"]) for g in goals) if goals else 0
    progress_pct = round((portfolio["total_value"] / goal_target) * 100, 2) if goal_target else 0

    return {
        "user": {"name": user["name"], "email": user["email"]},
        "profile": dict(profile) if profile else None,
        "portfolio": portfolio,
        "goals": [dict(g) for g in goals],
        "metrics": {
            "goal_target": round(goal_target, 2),
            "goal_monthly": round(goal_monthly, 2),
            "goal_progress_pct": progress_pct,
            "risk_badge": profile["risk_level"] if profile else "Not Set",
        },
        "disclaimer": "This app provides educational insights, not SEBI-registered investment advice.",
    }

