from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Budget, ExpenseCategory, Income, Expense
from ai import advisor

budget_bp = Blueprint("budget", __name__)


@budget_bp.route("/budget", methods=["GET"])
@login_required
def index():
    now = datetime.utcnow()
    month = int(request.args.get("month", now.month))
    year = int(request.args.get("year", now.year))

    budgets = Budget.query.filter_by(user_id=current_user.id, month=month, year=year).all()

    # Actual spend per category this month, to compare against budget
    spend_by_category = {}
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        db.extract("month", Expense.date) == month,
        db.extract("year", Expense.date) == year,
    ).all()
    for e in expenses:
        spend_by_category[e.category_id] = spend_by_category.get(e.category_id, 0) + e.amount

    return render_template(
        "budget.html",
        budgets=budgets,
        spend_by_category=spend_by_category,
        month=month,
        year=year,
    )


@budget_bp.route("/budget/generate", methods=["POST"])
@login_required
def generate():
    now = datetime.utcnow()
    month = int(request.form.get("month", now.month))
    year = int(request.form.get("year", now.year))

    categories = ExpenseCategory.query.filter_by(user_id=current_user.id).all()
    if not categories:
        flash("Add at least one expense category before generating a budget.", "warning")
        return redirect(url_for("budget.index", month=month, year=year))

    incomes = Income.query.filter(
        Income.user_id == current_user.id,
        db.extract("month", Income.date) == month,
        db.extract("year", Income.date) == year,
    ).all()
    total_income = sum(i.amount for i in incomes) or current_user.monthly_income_goal

    allocation = advisor.generate_budget(total_income, categories)

    # Clear existing budget for this month/year and replace with the new AI plan
    Budget.query.filter_by(user_id=current_user.id, month=month, year=year).delete()

    name_to_category = {c.name: c for c in categories}
    for name, amount in allocation.items():
        category = name_to_category.get(name)
        if category is None:
            continue
        db.session.add(
            Budget(
                user_id=current_user.id,
                category_id=category.id,
                month=month,
                year=year,
                planned_amount=round(float(amount), 2),
                ai_generated=True,
            )
        )
    db.session.commit()
    flash("AI-generated budget created for this month.", "success")
    return redirect(url_for("budget.index", month=month, year=year))


@budget_bp.route("/budget/manual", methods=["POST"])
@login_required
def manual():
    month = int(request.form.get("month"))
    year = int(request.form.get("year"))
    category_id = request.form.get("category_id")
    planned_amount = request.form.get("planned_amount")

    try:
        planned_amount = float(planned_amount)
    except (TypeError, ValueError):
        flash("Enter a valid planned amount.", "danger")
        return redirect(url_for("budget.index", month=month, year=year))

    category = ExpenseCategory.query.filter_by(id=category_id, user_id=current_user.id).first()
    if not category:
        flash("Invalid category.", "danger")
        return redirect(url_for("budget.index", month=month, year=year))

    existing = Budget.query.filter_by(
        user_id=current_user.id, category_id=category.id, month=month, year=year
    ).first()
    if existing:
        existing.planned_amount = planned_amount
        existing.ai_generated = False
    else:
        db.session.add(
            Budget(
                user_id=current_user.id,
                category_id=category.id,
                month=month,
                year=year,
                planned_amount=planned_amount,
                ai_generated=False,
            )
        )
    db.session.commit()
    flash("Budget entry saved.", "success")
    return redirect(url_for("budget.index", month=month, year=year))
