from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.extensions import db
from app.models import Resource, User
from app.decorators import login_required, admin_required
from app.constants import VALID_BRANCHES

resources_bp = Blueprint("resources", __name__, url_prefix="/resources")


@resources_bp.route("/")
@login_required
def index():
    user = User.query.get(session["user_id"])
    category = request.args.get("category", "notes")  # default tab = notes

    # A resource is visible if:
    # - branch is NULL (common for all branches) OR matches the student's branch
    # - AND year is NULL (common for all years) OR matches the student's year
    query = Resource.query.filter_by(category=category)
    query = query.filter(
        (Resource.branch.is_(None)) | (Resource.branch == user.branch)
    )
    query = query.filter(
        (Resource.year.is_(None)) | (Resource.year == user.year)
    )
    resource_list = query.order_by(Resource.created_at.desc()).all()

    return render_template(
        "resources/index.html",
        resources=resource_list,
        category=category,
        branches=VALID_BRANCHES,
        is_admin=(session.get("user_role") == "admin"),
    )


@resources_bp.route("/add", methods=["POST"])
@login_required
@admin_required
def add():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    file_link = request.form.get("file_link", "").strip()
    category = request.form.get("category", "notes")
    subject = request.form.get("subject", "").strip()
    branch = request.form.get("branch") or None   # empty string -> NULL (common)
    year = request.form.get("year") or None

    if not title:
        flash("Title is required.")
        return redirect(url_for("resources.index", category=category))

    resource = Resource(
        title=title,
        description=description,
        file_link=file_link,
        category=category,
        subject=subject,
        branch=branch,
        year=int(year) if year else None,
        created_by=session["user_id"],
    )
    db.session.add(resource)
    db.session.commit()

    flash("Resource added.")
    return redirect(url_for("resources.index", category=category))


@resources_bp.route("/edit/<int:resource_id>", methods=["POST"])
@login_required
@admin_required
def edit(resource_id):
    resource = Resource.query.get_or_404(resource_id)

    resource.title = request.form.get("title", resource.title).strip()
    resource.description = request.form.get("description", resource.description)
    resource.file_link = request.form.get("file_link", resource.file_link)
    resource.subject = request.form.get("subject", resource.subject)
    branch = request.form.get("branch")
    year = request.form.get("year")
    resource.branch = branch or None
    resource.year = int(year) if year else None

    db.session.commit()
    flash("Resource updated.")
    return redirect(url_for("resources.index", category=resource.category))


@resources_bp.route("/bulk", methods=["GET", "POST"])
@login_required
@admin_required
def bulk_add():
    default_category = request.args.get("category", "notes")

    if request.method == "POST":
        raw_text = request.form.get("bulk_text", "").strip()
        if not raw_text:
            flash("Please paste some resources.")
            return redirect(url_for("resources.bulk_add", category=default_category))

        # Defaults - can be overridden by meta lines, or per-resource
        current_category = default_category
        current_branch = None
        current_year = None

        lines = [line.strip() for line in raw_text.splitlines()]
        i = 0
        added_count = 0
        errors = []

        def is_meta_or_title(l):
            lower = l.lower()
            return (
                lower.startswith("title:") or lower.startswith("category:")
                or lower.startswith("branch:") or lower.startswith("year:")
            )

        while i < len(lines):
            line = lines[i]

            if not line:
                i += 1
                continue

            # Global meta lines (apply until overridden again)
            if line.lower().startswith("category:"):
                current_category = line.split(":", 1)[1].strip()
                i += 1
                continue
            if line.lower().startswith("branch:"):
                val = line.split(":", 1)[1].strip()
                current_branch = None if val.lower() in ("", "common", "all") else val
                i += 1
                continue
            if line.lower().startswith("year:"):
                val = line.split(":", 1)[1].strip()
                current_year = None if val.lower() in ("", "any") else val
                i += 1
                continue

            # Start of a resource
            if line.lower().startswith("title:"):
                title = line.split(":", 1)[1].strip()
                subject = ""
                link = ""
                description = ""
                branch = current_branch
                year = current_year

                i += 1
                while i < len(lines) and lines[i] and not is_meta_or_title(lines[i]):
                    field_line = lines[i]
                    if field_line.lower().startswith("subject:"):
                        subject = field_line.split(":", 1)[1].strip()
                    elif field_line.lower().startswith("link:"):
                        link = field_line.split(":", 1)[1].strip()
                    elif field_line.lower().startswith("description:"):
                        description = field_line.split(":", 1)[1].strip()
                    elif field_line.lower().startswith("resource branch:"):
                        val = field_line.split(":", 1)[1].strip()
                        branch = None if val.lower() in ("", "common", "all") else val
                    elif field_line.lower().startswith("resource year:"):
                        val = field_line.split(":", 1)[1].strip()
                        year = None if val.lower() in ("", "any") else val
                    i += 1

                if not title:
                    errors.append("Skipped a resource with no title.")
                    continue

                resource = Resource(
                    title=title,
                    description=description,
                    file_link=link,
                    category=current_category,
                    subject=subject,
                    branch=branch,
                    year=int(year) if year else None,
                    created_by=session["user_id"],
                )
                db.session.add(resource)
                added_count += 1
            else:
                i += 1

        if added_count > 0:
            db.session.commit()
            flash(f"Successfully added {added_count} resources.")
        if errors:
            flash(f"{len(errors)} resource(s) skipped: " + "; ".join(errors[:5]))

        return redirect(url_for("resources.index", category=current_category))

    return render_template("resources/bulk_add.html", category=default_category)


@resources_bp.route("/delete/<int:resource_id>", methods=["POST"])
@login_required
@admin_required
def delete(resource_id):
    resource = Resource.query.get_or_404(resource_id)
    category = resource.category
    db.session.delete(resource)
    db.session.commit()
    flash("Resource deleted.")
    return redirect(url_for("resources.index", category=category))
