from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.extensions import db
from app.models import DSATopic, DSAProgress
from app.decorators import login_required

dsa_bp = Blueprint("dsa", __name__, url_prefix="/dsa")


@dsa_bp.route("/")
@login_required
def index():
    user_id = session["user_id"]

    # Get all topics, ordered
    topics = DSATopic.query.order_by(DSATopic.order_index).all()

    # Get this user's progress as a dict: {topic_id: status}
    progress_rows = DSAProgress.query.filter_by(user_id=user_id).all()
    progress_map = {row.topic_id: row.status for row in progress_rows}

    # Build a combined list for the template
    topic_list = []
    for topic in topics:
        status = progress_map.get(topic.id, "Not Started")
        topic_list.append({"id": topic.id, "name": topic.name, "status": status})

    # Simple stats for a progress summary
    total = len(topic_list)
    completed = sum(1 for t in topic_list if t["status"] == "Completed")
    in_progress = sum(1 for t in topic_list if t["status"] == "In Progress")

    return render_template(
        "dsa/index.html",
        topics=topic_list,
        total=total,
        completed=completed,
        in_progress=in_progress,
    )


@dsa_bp.route("/update/<int:topic_id>", methods=["POST"])
@login_required
def update_status(topic_id):
    user_id = session["user_id"]
    new_status = request.form.get("status")

    valid_statuses = ["Not Started", "In Progress", "Completed"]
    if new_status not in valid_statuses:
        flash("Invalid status.")
        return redirect(url_for("dsa.index"))

    # Check if a progress row already exists for this user+topic
    progress = DSAProgress.query.filter_by(user_id=user_id, topic_id=topic_id).first()

    if progress:
        progress.status = new_status
    else:
        progress = DSAProgress(user_id=user_id, topic_id=topic_id, status=new_status)
        db.session.add(progress)

    db.session.commit()
    return redirect(url_for("dsa.index"))
