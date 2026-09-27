from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Expense, ExpenseCategory

expenses_bp = Blueprint("expenses", __name__)


@expenses_bp.route("/expenses", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        category_id = request.form.get("category_id")
        amount = request.form.get("amount", "")
        date_str = request.form.get("date", "")
        description = request.form.get("description", "").strip()

        try:
            amount = float(amount)
            date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.utcnow().date()
        except ValueError:
            flash("Please enter a valid amount and date.", "danger")
            return redirect(url_for("expenses.index"))

        category = ExpenseCategory.query.filter_by(id=category_id, user_id=current_user.id).first()
        if not category or amount <= 0:
            flash("Valid category and positive amount are required.", "danger")
            return redirect(url_for("expenses.index"))

        record = Expense(
            user_id=current_user.id,
            category_id=category.id,
            amount=amount,
            date=date,
            description=description,
        )
        db.session.add(record)
        db.session.commit()
        flash("Expense recorded.", "success")
        return redirect(url_for("expenses.index"))

    categories = ExpenseCategory.query.filter_by(user_id=current_user.id).all()
    records = (
        Expense.query.filter_by(user_id=current_user.id)
        .order_by(Expense.date.desc())
        .all()
    )
    total = sum(r.amount for r in records)
    return render_template("expenses.html", records=records, categories=categories, total=total)


@expenses_bp.route("/expenses/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete(expense_id):
    record = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    db.session.delete(record)
    db.session.commit()
    flash("Expense deleted.", "info")
    return redirect(url_for("expenses.index"))


@expenses_bp.route("/categories", methods=["GET", "POST"])
@login_required
def categories():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Category name is required.", "danger")
        elif ExpenseCategory.query.filter_by(user_id=current_user.id, name=name).first():
            flash("You already have a category with that name.", "danger")
        else:
            db.session.add(ExpenseCategory(user_id=current_user.id, name=name))
            db.session.commit()
            flash("Category added.", "success")
        return redirect(url_for("expenses.categories"))

    cats = ExpenseCategory.query.filter_by(user_id=current_user.id).all()
    return render_template("categories.html", categories=cats)


@expenses_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
def delete_category(category_id):
    category = ExpenseCategory.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    db.session.delete(category)
    db.session.commit()
    flash("Category deleted.", "info")
    return redirect(url_for("expenses.categories"))
