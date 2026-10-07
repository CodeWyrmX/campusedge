from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.extensions import db
from app.models import User, DSATopic, AptitudeQuestion
from app.decorators import login_required, admin_required
from app.constants import VALID_CATEGORIES, VALID_DIFFICULTIES

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@admin_required
def index():
    return render_template("admin/index.html")


# ---------------- User management ----------------

@admin_bp.route("/users")
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/toggle-role/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def toggle_role(user_id):
    if user_id == session["user_id"]:
        flash("You cannot change your own role.")
        return redirect(url_for("admin.users"))

    user = User.query.get_or_404(user_id)
    user.role = "admin" if user.role == "student" else "student"
    db.session.commit()
    flash(f"{user.name} is now {user.role}.")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/delete/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == session["user_id"]:
        flash("You cannot delete your own account.")
        return redirect(url_for("admin.users"))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.")
    return redirect(url_for("admin.users"))


# ---------------- DSA topics management ----------------

@admin_bp.route("/dsa-topics")
@login_required
@admin_required
def dsa_topics():
    topics = DSATopic.query.order_by(DSATopic.order_index).all()
    return render_template("admin/dsa_topics.html", topics=topics)


@admin_bp.route("/dsa-topics/add", methods=["POST"])
@login_required
@admin_required
def add_dsa_topic():
    name = request.form.get("name", "").strip()
    order_index = request.form.get("order_index", "0")

    if not name:
        flash("Topic name is required.")
        return redirect(url_for("admin.dsa_topics"))

    topic = DSATopic(name=name, order_index=int(order_index) if order_index else 0)
    db.session.add(topic)
    db.session.commit()
    flash("Topic added.")
    return redirect(url_for("admin.dsa_topics"))


@admin_bp.route("/dsa-topics/delete/<int:topic_id>", methods=["POST"])
@login_required
@admin_required
def delete_dsa_topic(topic_id):
    topic = DSATopic.query.get_or_404(topic_id)
    db.session.delete(topic)
    db.session.commit()
    flash("Topic deleted.")
    return redirect(url_for("admin.dsa_topics"))


# ---------------- Aptitude questions management ----------------

@admin_bp.route("/aptitude-questions")
@login_required
@admin_required
def aptitude_questions():
    questions = AptitudeQuestion.query.order_by(AptitudeQuestion.created_at.desc()).all()
    return render_template(
        "admin/aptitude_questions.html",
        questions=questions,
        categories=VALID_CATEGORIES,
        difficulties=VALID_DIFFICULTIES,
    )


@admin_bp.route("/aptitude-questions/add", methods=["POST"])
@login_required
@admin_required
def add_aptitude_question():
    question_text = request.form.get("question_text", "").strip()
    option_a = request.form.get("option_a", "").strip()
    option_b = request.form.get("option_b", "").strip()
    option_c = request.form.get("option_c", "").strip()
    option_d = request.form.get("option_d", "").strip()
    correct_option = request.form.get("correct_option", "A")
    category = request.form.get("category", "").strip()
    difficulty = request.form.get("difficulty", "Easy")
    test_number = request.form.get("test_number", "1")

    if not all([question_text, option_a, option_b, option_c, option_d]):
        flash("All question fields are required.")
        return redirect(url_for("admin.aptitude_questions"))

    try:
        test_number = int(test_number)
        if test_number < 1:
            test_number = 1
    except (ValueError, TypeError):
        test_number = 1

    question = AptitudeQuestion(
        question_text=question_text,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct_option=correct_option,
        category=category,
        difficulty=difficulty,
        test_number=test_number,
        created_by=session["user_id"],
    )
    db.session.add(question)
    db.session.commit()
    flash("Question added.")
    return redirect(url_for("admin.aptitude_questions"))


@admin_bp.route("/aptitude-questions/delete/<int:question_id>", methods=["POST"])
@login_required
@admin_required
def delete_aptitude_question(question_id):
    question = AptitudeQuestion.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted.")
    return redirect(url_for("admin.aptitude_questions"))


@admin_bp.route("/aptitude-questions/bulk", methods=["GET", "POST"])
@login_required
@admin_required
def bulk_add_aptitude():
    if request.method == "POST":
        raw_text = request.form.get("bulk_text", "").strip()
        if not raw_text:
            flash("Please paste some questions.")
            return redirect(url_for("admin.bulk_add_aptitude"))

        # Default values (can be overridden inside the text)
        current_category = "Quantitative Aptitude"
        current_difficulty = "Easy"
        current_test = 1

        lines = [line.strip() for line in raw_text.splitlines()]
        i = 0
        added_count = 0
        errors = []

        while i < len(lines):
            line = lines[i]

            # Meta lines
            if line.lower().startswith("category:"):
                current_category = line.split(":", 1)[1].strip()
                i += 1
                continue
            if line.lower().startswith("difficulty:"):
                current_difficulty = line.split(":", 1)[1].strip()
                i += 1
                continue
            if line.lower().startswith("test number:") or line.lower().startswith("test:"):
                try:
                    current_test = int(line.split(":", 1)[1].strip())
                except ValueError:
                    current_test = 1
                i += 1
                continue

            # Start of a question
            if line.lower().startswith("question:"):
                question_text = line.split(":", 1)[1].strip()
                options = {"A": "", "B": "", "C": "", "D": ""}
                correct = None

                i += 1
                # Collect next lines for options + correct
                while i < len(lines):
                    opt_line = lines[i]
                    if opt_line.lower().startswith("question:") or \
                       opt_line.lower().startswith("category:") or \
                       opt_line.lower().startswith("difficulty:") or \
                       opt_line.lower().startswith("test"):
                        break

                    if opt_line.upper().startswith("A.") or opt_line.upper().startswith("A)"):
                        options["A"] = opt_line[2:].strip()
                    elif opt_line.upper().startswith("B.") or opt_line.upper().startswith("B)"):
                        options["B"] = opt_line[2:].strip()
                    elif opt_line.upper().startswith("C.") or opt_line.upper().startswith("C)"):
                        options["C"] = opt_line[2:].strip()
                    elif opt_line.upper().startswith("D.") or opt_line.upper().startswith("D)"):
                        options["D"] = opt_line[2:].strip()
                    elif opt_line.lower().startswith("correct:"):
                        correct = opt_line.split(":", 1)[1].strip().upper()
                        if correct not in ["A", "B", "C", "D"]:
                            correct = None
                    i += 1

                # Validate
                if not question_text or not all(options.values()) or not correct:
                    errors.append(f"Skipped incomplete question: {question_text[:40]}...")
                    continue

                question = AptitudeQuestion(
                    question_text=question_text,
                    option_a=options["A"],
                    option_b=options["B"],
                    option_c=options["C"],
                    option_d=options["D"],
                    correct_option=correct,
                    category=current_category,
                    difficulty=current_difficulty,
                    test_number=current_test,
                    created_by=session["user_id"],
                )
                db.session.add(question)
                added_count += 1
            else:
                i += 1

        if added_count > 0:
            db.session.commit()
            flash(f"Successfully added {added_count} questions.")
        if errors:
            flash("Some questions were skipped (incomplete data).")

        return redirect(url_for("admin.aptitude_questions"))

    return render_template("admin/bulk_aptitude.html")
