# Personal Finance Advisor Bot

An AI-powered personal finance management platform built with **Flask, SQLAlchemy,
SQLite/PostgreSQL, Jinja2, and ChatGPT/Gemini AI**. Users can record income, track
expenses, generate AI-powered budgets, receive personalized financial recommendations,
and monitor performance through an interactive dashboard and monthly reports.

## Features

- 🔐 Secure user authentication (Flask-Login, hashed passwords, protected routes)
- 💵 Income tracking with source, amount, date, and notes
- 🧾 Expense tracking with custom categories
- 🤖 AI-generated monthly budgets (OpenAI, Gemini, or a built-in rule-based fallback)
- 💡 AI-powered financial recommendations (overspending alerts, cost optimization tips)
- 📊 Interactive dashboard (Chart.js) — income/expense breakdown, budget vs. actual
- 📅 Monthly financial reports with category-wise analytics
- 🌐 One-command public deployment via Ngrok

## Project Structure

```
finance_bot/
├── app.py                 # Flask application factory
├── config.py               # Configuration from environment variables
├── extensions.py            # db, login_manager singletons
├── models.py                # SQLAlchemy models
├── requirements.txt
├── .env.example
├── ai/
│   └── advisor.py           # AI budget generation & recommendations (OpenAI/Gemini/rule-based)
├── routes/
│   ├── auth.py               # register/login/logout
│   ├── income.py              # income CRUD
│   ├── expenses.py            # expense + category CRUD
│   ├── budget.py               # AI + manual budget planning
│   └── dashboard.py            # dashboard, recommendations, reports
├── templates/                  # Jinja2 templates (Bootstrap 5 + Chart.js)
└── static/css/style.css
```

## 1. Local Setup

```bash
cd finance_bot
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- Set `FLASK_SECRET_KEY` to a random string.
- Leave `AI_PROVIDER=none` to use the built-in rule-based advisor (no API key needed),
  or set `AI_PROVIDER=openai` / `AI_PROVIDER=gemini` and fill in the matching API key
  to use real generative AI.
- Leave `DATABASE_URL` as-is for SQLite, or point it at a PostgreSQL instance.

## 2. Run the App

```bash
python app.py
```

The app creates its database tables automatically on first run and serves at
`http://127.0.0.1:5000`.

Sign up for an account, add a couple of expense categories (e.g. Rent, Groceries,
Transport), log some income and expenses, then visit **Budget** to generate an
AI-powered plan and **Dashboard** for visual insights.

## 3. Public Deployment with Ngrok

Install ngrok and authenticate once:

```bash
pip install pyngrok
ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN
```

Then either run ngrok alongside the app manually:

```bash
# terminal 1
python app.py

# terminal 2
ngrok http 5000
```

...or use the included snippet to launch both from one script — add this to the
bottom of `app.py` in place of `app.run(...)` if you want ngrok to start automatically:

```python
from pyngrok import ngrok
public_url = ngrok.connect(5000)
print(f" * Public URL: {public_url}")
app.run(debug=app.config["DEBUG"])
```

Ngrok will print a public HTTPS URL you can share for demos or external testing.

## 4. Testing Checklist

This mirrors the validation plan the project was scoped against:

- [ ] User registration, login, logout, and protected-route redirects
- [ ] Income add/list/delete
- [ ] Expense category add/delete, expense add/list/delete
- [ ] AI budget generation (with `AI_PROVIDER=none`, `openai`, and `gemini`)
- [ ] Budget vs. actual comparison updates correctly after new expenses
- [ ] AI recommendation generation and display
- [ ] Dashboard charts render correctly with real data
- [ ] Monthly report reflects correct totals and percentages
- [ ] Full flow accessible through an Ngrok public URL

## Tech Stack

Flask · SQLAlchemy · Flask-Login · SQLite/PostgreSQL · Jinja2 · Bootstrap 5 ·
Chart.js · OpenAI / Gemini API · python-dotenv · Ngrok

## Ideal For

AI Developers, Full-Stack Developers, FinTech Engineers, Backend Developers,
Software Engineers, Data Analysts, Generative AI Engineers, and students building
hands-on experience with Generative AI, FinTech, full-stack development, database
design, and prompt engineering.
