from datetime import datetime
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from extensions import db
from models import Income, Expense, ExpenseCategory, Budget, Recommendation
from ai import advisor

dashboard_bp = Blueprint("dashboard", __name__)


def _month_totals(user_id, month, year):
    incomes = Income.query.filter(
        Income.user_id == user_id,
        db.extract("month", Income.date) == month,
        db.extract("year", Income.date) == year,
    ).all()
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        db.extract("month", Expense.date) == month,
        db.extract("year", Expense.date) == year,
    ).all()

    total_income = sum(i.amount for i in incomes)
    total_expenses = sum(e.amount for e in expenses)

    category_totals = {}
    for e in expenses:
        cat_name = e.category.name if e.category else "Uncategorized"
        category_totals[cat_name] = category_totals.get(cat_name, 0) + e.amount

    return total_income, total_expenses, category_totals


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    now = datetime.utcnow()
    month = int(request.args.get("month", now.month))
    year = int(request.args.get("year", now.year))

    total_income, total_expenses, category_totals = _month_totals(current_user.id, month, year)
    net = total_income - total_expenses
    savings_progress = 0
    if current_user.savings_goal and current_user.savings_goal > 0:
        savings_progress = min(100, round((max(net, 0) / current_user.savings_goal) * 100, 1))

    budgets = Budget.query.filter_by(user_id=current_user.id, month=month, year=year).all()
    budget_vs_actual = []
    for b in budgets:
        actual = category_totals.get(b.category.name, 0)
        budget_vs_actual.append(
            {
                "category": b.category.name,
                "planned": b.planned_amount,
                "actual": actual,
                "over": actual > b.planned_amount,
            }
        )

    recent_recs = (
        Recommendation.query.filter_by(user_id=current_user.id)
        .order_by(Recommendation.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard.html",
        total_income=total_income,
        total_expenses=total_expenses,
        net=net,
        savings_progress=savings_progress,
        category_totals=category_totals,
        budget_vs_actual=budget_vs_actual,
        recommendations=recent_recs,
        month=month,
        year=year,
    )


@dashboard_bp.route("/recommendations/generate", methods=["POST"])
@login_required
def generate_recommendations():
    now = datetime.utcnow()
    month = int(request.form.get("month", now.month))
    year = int(request.form.get("year", now.year))

    total_income, total_expenses, category_totals = _month_totals(current_user.id, month, year)
    recs = advisor.generate_recommendations(total_income, total_expenses, category_totals)

    for text in recs:
        db.session.add(Recommendation(user_id=current_user.id, content=text, rec_type="ai"))
    db.session.commit()

    from flask import redirect, url_for, flash
    flash("New AI recommendations generated.", "success")
    return redirect(url_for("dashboard.index", month=month, year=year))


@dashboard_bp.route("/report")
@login_required
def report():
    now = datetime.utcnow()
    month = int(request.args.get("month", now.month))
    year = int(request.args.get("year", now.year))

    total_income, total_expenses, category_totals = _month_totals(current_user.id, month, year)
    savings = total_income - total_expenses
    budgets = Budget.query.filter_by(user_id=current_user.id, month=month, year=year).all()

    return render_template(
        "report.html",
        total_income=total_income,
        total_expenses=total_expenses,
        savings=savings,
        category_totals=category_totals,
        budgets=budgets,
        month=month,
        year=year,
    )
