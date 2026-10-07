from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models import User
from app.decorators import login_required
from app.constants import VALID_BRANCHES

profile_bp = Blueprint("profile", __name__)

VALID_YEARS = [1, 2, 3, 4]


@profile_bp.route("/profile", methods=["GET", "POST"])
@login_required
def index():
    user = User.query.get(session["user_id"])

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        branch = request.form.get("branch", "")
        year = request.form.get("year", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        current_password = request.form.get("current_password", "")

        # --- basic validation ---
        if not name or not branch or not year:
            flash("Name, branch and year are required.")
            return redirect(url_for("profile.index"))

        if branch not in VALID_BRANCHES:
            flash("Please select a valid branch.")
            return redirect(url_for("profile.index"))

        try:
            year_int = int(year)
        except ValueError:
            year_int = None

        if year_int not in VALID_YEARS:
            flash("Please select a valid year.")
            return redirect(url_for("profile.index"))

        # --- optional password change ---
        if new_password or confirm_password or current_password:
            if not current_password or not check_password_hash(user.password_hash, current_password):
                flash("Current password is incorrect. Profile details were not changed.")
                return redirect(url_for("profile.index"))

            if new_password != confirm_password:
                flash("New password and confirm password do not match.")
                return redirect(url_for("profile.index"))

            if len(new_password) < 6:
                flash("New password must be at least 6 characters.")
                return redirect(url_for("profile.index"))

            user.password_hash = generate_password_hash(new_password)

        # --- apply updates ---
        user.name = name
        user.branch = branch
        user.year = year_int
        db.session.commit()

        # Keep session display values in sync
        session["user_name"] = user.name

        flash("Profile updated successfully.")
        return redirect(url_for("profile.index"))

    return render_template("profile/index.html", user=user, branches=VALID_BRANCHES, years=VALID_YEARS)
