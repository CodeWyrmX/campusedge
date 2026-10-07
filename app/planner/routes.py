from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.extensions import db
from app.models import Task
from app.decorators import login_required

planner_bp = Blueprint("planner", __name__, url_prefix="/planner")


@planner_bp.route("/")
@login_required
def index():
    user_id = session["user_id"]

    pending_tasks = (
        Task.query.filter_by(user_id=user_id, status="Pending")
        .order_by(Task.due_date.asc())
        .all()
    )
    completed_tasks = (
        Task.query.filter_by(user_id=user_id, status="Completed")
        .order_by(Task.due_date.desc())
        .all()
    )

    return render_template(
        "planner/index.html",
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
    )


@planner_bp.route("/add", methods=["POST"])
@login_required
def add():
    user_id = session["user_id"]
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    due_date_str = request.form.get("due_date", "")

    if not title:
        flash("Task title is required.")
        return redirect(url_for("planner.index"))

    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except ValueError:
            due_date = None

    task = Task(
        user_id=user_id,
        title=title,
        description=description,
        due_date=due_date,
        status="Pending",
    )
    db.session.add(task)
    db.session.commit()

    flash("Task added.")
    return redirect(url_for("planner.index"))


@planner_bp.route("/edit/<int:task_id>", methods=["POST"])
@login_required
def edit(task_id):
    user_id = session["user_id"]
    task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()

    task.title = request.form.get("title", task.title).strip()
    task.description = request.form.get("description", task.description)
    due_date_str = request.form.get("due_date", "")

    if due_date_str:
        try:
            task.due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    db.session.commit()
    flash("Task updated.")
    return redirect(url_for("planner.index"))


@planner_bp.route("/complete/<int:task_id>", methods=["POST"])
@login_required
def complete(task_id):
    user_id = session["user_id"]
    task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()

    task.status = "Completed" if task.status == "Pending" else "Pending"
    db.session.commit()
    return redirect(url_for("planner.index"))


@planner_bp.route("/delete/<int:task_id>", methods=["POST"])
@login_required
def delete(task_id):
    user_id = session["user_id"]
    task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()

    db.session.delete(task)
    db.session.commit()
    flash("Task deleted.")
    return redirect(url_for("planner.index"))
