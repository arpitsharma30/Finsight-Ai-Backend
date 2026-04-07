def classify_risk(age: int, monthly_savings: int, loss_reaction: int) -> tuple[str, int]:
    score = 0
    score += 3 if age < 25 else 2 if age < 35 else 1
    score += 3 if monthly_savings > 10000 else 2 if monthly_savings > 5000 else 1
    score += max(1, min(3, loss_reaction))

    if score <= 4:
        return "Low", score
    if score <= 7:
        return "Medium", score
    return "High", score


def recommendation_text(risk_level: str, goal: str) -> tuple[str, str]:
    if risk_level == "Low":
        advice = "Build emergency fund first, then prioritize debt funds and index SIPs."
    elif risk_level == "Medium":
        advice = "Use diversified equity index SIP + balanced funds with disciplined monthly investing."
    else:
        advice = "Focus on equity-heavy diversified portfolio, cap single-stock exposure, and rebalance quarterly."

    ai_advice = (
        f"For your goal ({goal}), invest consistently every month, keep emergency cash for 6 months, "
        f"and follow a {risk_level.lower()}-risk allocation with periodic rebalancing."
    )
    return advice, ai_advice

