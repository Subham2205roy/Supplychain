# backend/ml/scoring.py

CAPITAL_MAP = {
    "Low": 0.3,
    "Medium": 0.6,
    "High": 1.0
}

TEAM_MAP = {
    "Solo": 0.3,
    "Small": 0.6,
    "Strong": 1.0
}

STAGE_MAP = {
    "Idea": 0.5,
    "Existing": 0.8
}

MARKET_MAP = {
    "Local": 0.4,
    "National": 0.7,
    "Global": 1.0
}


def calculate_rule_scores(
    market_demand,
    competition,
    differentiation,
    capital_range,
    profit_margin,
    founder_experience,
    team_strength,
    business_stage,
    target_market
):
    # Market score
    market_score = (
        (market_demand / 10) * 0.4 +
        (differentiation / 10) * 0.4 +
        ((10 - competition) / 10) * 0.2
    )

    # Financial score
    financial_score = (
        CAPITAL_MAP.get(capital_range, 0.3) * 0.6 +
        (profit_margin / 50) * 0.4
    )

    # Execution score
    execution_score = (
        (founder_experience / 10) * 0.5 +
        TEAM_MAP.get(team_strength, 0.3) * 0.5
    )

    # Context boost
    context_score = (
        STAGE_MAP.get(business_stage, 0.5) * 0.5 +
        MARKET_MAP.get(target_market, 0.4) * 0.5
    )

    return {
        "market_score": round(market_score, 2),
        "financial_score": round(financial_score, 2),
        "execution_score": round(execution_score, 2),
        "context_score": round(context_score, 2)
    }
