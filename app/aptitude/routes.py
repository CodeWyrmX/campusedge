from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.extensions import db
from app.models import AptitudeQuestion, AptitudeAttempt
from app.decorators import login_required
from app.constants import VALID_CATEGORIES, VALID_DIFFICULTIES
from sqlalchemy import func

aptitude_bp = Blueprint("aptitude", __name__, url_prefix="/aptitude")


@aptitude_bp.route("/")
@login_required
def index():
    """Step 1 - Select Category"""
    return render_template(
        "aptitude/index.html",
        categories=VALID_CATEGORIES,
    )


@aptitude_bp.route("/<path:category>")
@login_required
def select_difficulty(category):
    """Step 2 - Select Difficulty"""
    if category not in VALID_CATEGORIES:
        flash("Invalid category.")
        return redirect(url_for("aptitude.index"))

    return render_template(
        "aptitude/difficulty.html",
        category=category,
        difficulties=VALID_DIFFICULTIES,
    )


@aptitude_bp.route("/<path:category>/<difficulty>")
@login_required
def select_test(category, difficulty):
    """Step 3 - Select Test Number"""
    if category not in VALID_CATEGORIES or difficulty not in VALID_DIFFICULTIES:
        flash("Invalid category or difficulty.")
        return redirect(url_for("aptitude.index"))

    # Find all distinct test_numbers that have questions for this category + difficulty
    tests = (
        db.session.query(
            AptitudeQuestion.test_number,
            func.count(AptitudeQuestion.id).label("question_count")
        )
        .filter_by(category=category, difficulty=difficulty)
        .group_by(AptitudeQuestion.test_number)
        .order_by(AptitudeQuestion.test_number)
        .all()
    )

    return render_template(
        "aptitude/tests.html",
        category=category,
        difficulty=difficulty,
        tests=tests,
    )


@aptitude_bp.route("/<path:category>/<difficulty>/<int:test_number>")
@login_required
def take_quiz(category, difficulty, test_number):
    """Actual Quiz page - shows only the questions of that specific test"""
    if category not in VALID_CATEGORIES or difficulty not in VALID_DIFFICULTIES:
        flash("Invalid category or difficulty.")
        return redirect(url_for("aptitude.index"))

    questions = (
        AptitudeQuestion.query
        .filter_by(
            category=category,
            difficulty=difficulty,
            test_number=test_number
        )
        .order_by(AptitudeQuestion.id)
        .all()
    )

    if not questions:
        flash("No questions found for this test.")
        return redirect(url_for("aptitude.select_test", category=category, difficulty=difficulty))

    return render_template(
        "aptitude/quiz.html",
        questions=questions,
        category=category,
        difficulty=difficulty,
        test_number=test_number,
    )


@aptitude_bp.route("/submit", methods=["POST"])
@login_required
def submit():
    user_id = session["user_id"]

    category = request.form.get("category")
    difficulty = request.form.get("difficulty")
    test_number = request.form.get("test_number")

    try:
        test_number = int(test_number)
    except (TypeError, ValueError):
        flash("Invalid test.")
        return redirect(url_for("aptitude.index"))

    # Fetch the exact same set of questions the student saw
    questions = (
        AptitudeQuestion.query
        .filter_by(
            category=category,
            difficulty=difficulty,
            test_number=test_number
        )
        .all()
    )

    score = 0
    total = len(questions)

    for question in questions:
        submitted = request.form.get(f"question_{question.id}")
        if submitted == question.correct_option:
            score += 1

    attempt = AptitudeAttempt(
        user_id=user_id,
        score=score,
        total_questions=total,
        category=category,
        difficulty=difficulty,
        test_number=test_number,
    )
    db.session.add(attempt)
    db.session.commit()

    return render_template(
        "aptitude/result.html",
        score=score,
        total=total,
        category=category,
        difficulty=difficulty,
        test_number=test_number,
    )


@aptitude_bp.route("/history")
@login_required
def history():
    user_id = session["user_id"]
    attempts = (
        AptitudeAttempt.query
        .filter_by(user_id=user_id)
        .order_by(AptitudeAttempt.taken_at.desc())
        .all()
    )
    return render_template("aptitude/history.html", attempts=attempts)
