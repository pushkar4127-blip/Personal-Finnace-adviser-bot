"""
AI-powered financial advisory engine.

Supports three modes, controlled by config.AI_PROVIDER:
  - "openai": uses the OpenAI API to generate budgets & recommendations
  - "gemini": uses the Google Gemini API
  - "none"  : uses a transparent rule-based fallback (50/30/20 style rule)
              so the app is fully functional without any API key.
"""
import json
from flask import current_app


def _rule_based_budget(total_income, categories):
    """
    Fallback budget generator using a 50/30/20-inspired split:
    50% needs, 30% wants, 20% savings — distributed evenly across
    the user's existing categories as a starting point.
    """
    if not categories:
        return {}
    needs_pool = total_income * 0.50
    wants_pool = total_income * 0.30
    # Simple heuristic: alternate assigning categories to needs/wants pools
    per_category = (needs_pool + wants_pool) / max(len(categories), 1)
    return {cat.name: round(per_category, 2) for cat in categories}


def _rule_based_recommendations(total_income, total_expenses, category_totals):
    recs = []
    if total_expenses > total_income:
        recs.append(
            "You're spending more than you earn this period. Review discretionary "
            "categories first and look for quick cuts before the next billing cycle."
        )
    elif total_income > 0 and total_expenses / total_income < 0.7:
        recs.append(
            "Great job — you're spending well within your income. Consider directing "
            "the surplus toward an emergency fund or a savings goal."
        )
    if category_totals:
        top_cat = max(category_totals, key=category_totals.get)
        recs.append(
            f"'{top_cat}' is your largest expense category. Small reductions here "
            "will have the biggest impact on your overall budget."
        )
    recs.append(
        "Aim to keep 3–6 months of expenses in an easily accessible emergency fund."
    )
    return recs


def generate_budget(total_income, categories):
    """Returns dict {category_name: planned_amount}."""
    provider = current_app.config.get("AI_PROVIDER", "none")

    if provider == "openai" and current_app.config.get("OPENAI_API_KEY"):
        try:
            return _openai_budget(total_income, categories)
        except Exception as e:
            current_app.logger.warning(f"OpenAI budget generation failed, falling back: {e}")

    if provider == "gemini" and current_app.config.get("GEMINI_API_KEY"):
        try:
            return _gemini_budget(total_income, categories)
        except Exception as e:
            current_app.logger.warning(f"Gemini budget generation failed, falling back: {e}")

    return _rule_based_budget(total_income, categories)


def generate_recommendations(total_income, total_expenses, category_totals):
    """Returns a list of recommendation strings."""
    provider = current_app.config.get("AI_PROVIDER", "none")

    if provider == "openai" and current_app.config.get("OPENAI_API_KEY"):
        try:
            return _openai_recommendations(total_income, total_expenses, category_totals)
        except Exception as e:
            current_app.logger.warning(f"OpenAI recommendation generation failed, falling back: {e}")

    if provider == "gemini" and current_app.config.get("GEMINI_API_KEY"):
        try:
            return _gemini_recommendations(total_income, total_expenses, category_totals)
        except Exception as e:
            current_app.logger.warning(f"Gemini recommendation generation failed, falling back: {e}")

    return _rule_based_recommendations(total_income, total_expenses, category_totals)


# ---------------------------------------------------------------------------
# OpenAI integration
# ---------------------------------------------------------------------------

def _openai_client():
    from openai import OpenAI
    return OpenAI(api_key=current_app.config["OPENAI_API_KEY"])


def _openai_budget(total_income, categories):
    client = _openai_client()
    category_names = [c.name for c in categories]
    prompt = (
        f"A user has a total monthly income of {total_income}. "
        f"Their expense categories are: {category_names}. "
        "Suggest a monthly budget allocation across these categories using sound "
        "personal finance principles (e.g. needs/wants/savings balance). "
        'Respond ONLY with valid JSON in the form {"CategoryName": amount, ...} '
        "with no extra commentary."
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )
    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


def _openai_recommendations(total_income, total_expenses, category_totals):
    client = _openai_client()
    prompt = (
        f"Total income: {total_income}. Total expenses: {total_expenses}. "
        f"Spending by category: {category_totals}. "
        "Give 3-5 short, specific, actionable personal finance recommendations. "
        'Respond ONLY with valid JSON: {"recommendations": ["...", "..."]}'
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )
    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text).get("recommendations", [])


# ---------------------------------------------------------------------------
# Gemini integration
# ---------------------------------------------------------------------------

def _gemini_request(prompt):
    import requests
    api_key = current_app.config["GEMINI_API_KEY"]
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={api_key}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return text.replace("```json", "").replace("```", "").strip()


def _gemini_budget(total_income, categories):
    category_names = [c.name for c in categories]
    prompt = (
        f"A user has a total monthly income of {total_income}. "
        f"Their expense categories are: {category_names}. "
        "Suggest a monthly budget allocation across these categories using sound "
        "personal finance principles. "
        'Respond ONLY with valid JSON: {"CategoryName": amount, ...}'
    )
    return json.loads(_gemini_request(prompt))


def _gemini_recommendations(total_income, total_expenses, category_totals):
    prompt = (
        f"Total income: {total_income}. Total expenses: {total_expenses}. "
        f"Spending by category: {category_totals}. "
        "Give 3-5 short, specific, actionable personal finance recommendations. "
        'Respond ONLY with valid JSON: {"recommendations": ["...", "..."]}'
    )
    return json.loads(_gemini_request(prompt)).get("recommendations", [])
