from fastapi import APIRouter
from pydantic import BaseModel
import os
import json
from groq import Groq

router = APIRouter()

class QuizRequest(BaseModel):
    topic: str = "finance basics"

class RiskRequest(BaseModel):
    age: int
    monthly_savings: int
    income: int
    loss_reaction: int


FALLBACK_QUIZ = [
    {
        "question": "What is a mutual fund?",
        "options": [
            "A single stock investment",
            "A pool of investor money managed professionally",
            "A type of government bond",
            "A savings account",
        ],
        "correct": 1,
        "explanation": "A mutual fund pools money from multiple investors and invests in a diversified portfolio managed by professionals.",
    },
    {
        "question": "What does SIP stand for in investing?",
        "options": [
            "Stock Investment Plan",
            "Systematic Investment Plan",
            "Secure Investment Portfolio",
            "Simple Index Purchase",
        ],
        "correct": 1,
        "explanation": "SIP (Systematic Investment Plan) lets you invest a fixed amount at regular intervals, helping build wealth through rupee cost averaging.",
    },
    {
        "question": "What is the P/E ratio used for?",
        "options": [
            "Measuring company debt",
            "Valuing a stock relative to earnings",
            "Calculating dividend yield",
            "Tracking revenue growth",
        ],
        "correct": 1,
        "explanation": "The Price-to-Earnings ratio compares stock price to earnings per share, helping assess if a stock is over or undervalued.",
    },
    {
        "question": "What is an index fund?",
        "options": [
            "A fund managed by an expert to beat the market",
            "A fund that tracks a market index like Nifty 50",
            "A fund that only invests in bonds",
            "A fund for high-net-worth individuals",
        ],
        "correct": 1,
        "explanation": "An index fund passively tracks a market index like Nifty 50, offering broad market exposure at very low fees.",
    },
    {
        "question": "Which is generally considered lower risk?",
        "options": [
            "Individual stocks",
            "Cryptocurrency",
            "Diversified mutual fund",
            "Penny stocks",
        ],
        "correct": 2,
        "explanation": "Diversified mutual funds spread risk across many assets, making them generally safer than individual stocks or crypto.",
    },
]

@router.post("/quiz")
async def get_quiz(req: QuizRequest):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"questions": FALLBACK_QUIZ}

    prompt = f"""Generate 5 multiple choice questions about {req.topic} for students learning finance.
Return ONLY a JSON array, no extra text, no markdown:
[
  {{
    "question": "What is a mutual fund?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct": 1,
    "explanation": "Brief explanation here"
  }}
]"""

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        text = response.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()

        try:
            questions = json.loads(text)
        except json.JSONDecodeError:
            # Attempt to recover JSON array if the model returns extra text.
            start = text.find('[')
            end = text.rfind(']')
            if start != -1 and end != -1 and end > start:
                questions = json.loads(text[start : end + 1])
            else:
                raise

        if not isinstance(questions, list) or not questions:
            return {"questions": FALLBACK_QUIZ}

        return {"questions": questions}
    except Exception:
        return {"questions": FALLBACK_QUIZ}


@router.post("/quiz/risk")
async def assess_risk(req: RiskRequest):
    api_key = os.getenv("GROQ_API_KEY")
    score = 0

    if req.age < 25:       score += 3
    elif req.age < 35:     score += 2
    else:                  score += 1

    if req.monthly_savings > 10000:   score += 3
    elif req.monthly_savings > 5000:  score += 2
    else:                             score += 1

    score += req.loss_reaction

    if score <= 4:
        risk = "Low"
        advice = "Stick to FDs and government bonds. Safe and steady!"
    elif score <= 7:
        risk = "Medium"
        advice = "Mix of mutual funds and some stocks works great for you!"
    else:
        risk = "High"
        advice = "You can explore stocks and equity funds. But diversify!"

    ai_prompt = f"A student has a {risk} risk appetite with score {score}/9. Give them 3 specific investment tips in 2 sentences total. Be concise."
    ai_advice = advice
    if api_key:
        try:
            client = Groq(api_key=api_key)
            ai_response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": ai_prompt}],
                temperature=0.7,
            )
            ai_advice = ai_response.choices[0].message.content.strip()
        except Exception:
            ai_advice = advice

    return {
        "risk_level": risk,
        "score":      score,
        "max_score":  9,
        "advice":     advice,
        "ai_advice":  ai_advice,
    }