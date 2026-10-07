from flask import Blueprint, render_template, session
from app.decorators import login_required
from app.models import DSATopic, DSAProgress, AptitudeAttempt, Task

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    user_id = session["user_id"]

    # --- DSA stats ---
    total_topics = DSATopic.query.count()
    completed_topics = DSAProgress.query.filter_by(user_id=user_id, status="Completed").count()
    dsa_percent = round((completed_topics / total_topics) * 100) if total_topics > 0 else 0

    # --- Aptitude stats ---
    attempts = AptitudeAttempt.query.filter_by(user_id=user_id).all()
    attempt_count = len(attempts)
    if attempt_count > 0:
        avg_percent = round(
            sum((a.score / a.total_questions) * 100 for a in attempts if a.total_questions) / attempt_count
        )
        latest_attempt = max(attempts, key=lambda a: a.taken_at)
    else:
        avg_percent = None
        latest_attempt = None

    # --- Planner stats ---
    pending_count = Task.query.filter_by(user_id=user_id, status="Pending").count()
    completed_task_count = Task.query.filter_by(user_id=user_id, status="Completed").count()

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name"),
        user_role=session.get("user_role"),
        total_topics=total_topics,
        completed_topics=completed_topics,
        dsa_percent=dsa_percent,
        attempt_count=attempt_count,
        avg_percent=avg_percent,
        latest_attempt=latest_attempt,
        pending_count=pending_count,
        completed_task_count=completed_task_count,
    )
