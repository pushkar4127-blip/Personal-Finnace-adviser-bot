from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Income

income_bp = Blueprint("income", __name__)


@income_bp.route("/income", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        source = request.form.get("source", "").strip()
        amount = request.form.get("amount", "")
        date_str = request.form.get("date", "")
        description = request.form.get("description", "").strip()

        try:
            amount = float(amount)
            date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.utcnow().date()
        except ValueError:
            flash("Please enter a valid amount and date.", "danger")
            return redirect(url_for("income.index"))

        if not source or amount <= 0:
            flash("Source and a positive amount are required.", "danger")
            return redirect(url_for("income.index"))

        record = Income(
            user_id=current_user.id,
            source=source,
            amount=amount,
            date=date,
            description=description,
        )
        db.session.add(record)
        db.session.commit()
        flash("Income recorded.", "success")
        return redirect(url_for("income.index"))

    records = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc()).all()
    total = sum(r.amount for r in records)
    return render_template("income.html", records=records, total=total)


@income_bp.route("/income/<int:income_id>/delete", methods=["POST"])
@login_required
def delete(income_id):
    record = Income.query.filter_by(id=income_id, user_id=current_user.id).first_or_404()
    db.session.delete(record)
    db.session.commit()
    flash("Income record deleted.", "info")
    return redirect(url_for("income.index"))
