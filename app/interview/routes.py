from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.extensions import db
from app.models import InterviewQuestion, User
from app.decorators import login_required, admin_required
from app.constants import VALID_BRANCHES

interview_bp = Blueprint("interview", __name__, url_prefix="/interview")


@interview_bp.route("/")
@login_required
def index():
    user = User.query.get(session["user_id"])
    q_type = request.args.get("type", "technical")  # default tab

    # Visible if branch is NULL (common) or matches the student's branch
    query = InterviewQuestion.query.filter_by(type=q_type)
    query = query.filter(
        (InterviewQuestion.branch.is_(None)) | (InterviewQuestion.branch == user.branch)
    )
    questions = query.order_by(InterviewQuestion.created_at.desc()).all()

    return render_template(
        "interview/index.html",
        questions=questions,
        q_type=q_type,
        branches=VALID_BRANCHES,
        is_admin=(session.get("user_role") == "admin"),
    )


@interview_bp.route("/add", methods=["POST"])
@login_required
@admin_required
def add():
    question_text = request.form.get("question", "").strip()
    model_answer = request.form.get("model_answer", "").strip()
    q_type = request.form.get("type", "technical")
    branch = request.form.get("branch") or None

    if not question_text:
        flash("Question text is required.")
        return redirect(url_for("interview.index", type=q_type))

    question = InterviewQuestion(
        question=question_text,
        model_answer=model_answer,
        type=q_type,
        branch=branch,
        created_by=session["user_id"],
    )
    db.session.add(question)
    db.session.commit()

    flash("Question added.")
    return redirect(url_for("interview.index", type=q_type))


@interview_bp.route("/edit/<int:question_id>", methods=["POST"])
@login_required
@admin_required
def edit(question_id):
    question = InterviewQuestion.query.get_or_404(question_id)

    question.question = request.form.get("question", question.question).strip()
    question.model_answer = request.form.get("model_answer", question.model_answer)
    branch = request.form.get("branch")
    question.branch = branch or None

    db.session.commit()
    flash("Question updated.")
    return redirect(url_for("interview.index", type=question.type))


@interview_bp.route("/delete/<int:question_id>", methods=["POST"])
@login_required
@admin_required
def delete(question_id):
    question = InterviewQuestion.query.get_or_404(question_id)
    q_type = question.type
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted.")
    return redirect(url_for("interview.index", type=q_type))
