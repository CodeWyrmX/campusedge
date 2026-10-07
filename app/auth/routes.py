from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models import User
from app.constants import VALID_BRANCHES

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        branch = request.form.get("branch", "")
        year = request.form.get("year", "")

        # --- basic validation ---
        if not name or not email or not password or not branch or not year:
            flash("All fields are required.")
            return redirect(url_for("auth.register"))

        if branch not in VALID_BRANCHES:
            flash("Please select a valid branch.")
            return redirect(url_for("auth.register"))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("An account with this email already exists.")
            return redirect(url_for("auth.register"))

        # --- create user ---
        new_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role="student",
            branch=branch,
            year=int(year),
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please log in.")
        return redirect(url_for("auth.login"))

    return render_template("register.html", branches=VALID_BRANCHES)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_role"] = user.role
            flash(f"Welcome back, {user.name}!")
            return redirect(url_for("dashboard.index"))
        else:
            flash("Invalid email or password.")
            return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("auth.login"))
