from datetime import datetime
from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("student", "admin", name="role_enum"), default="student")
    branch = db.Column(db.String(50))
    year = db.Column(db.Integer)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)


class Resource(db.Model):
    __tablename__ = "resources"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_link = db.Column(db.String(500))
    category = db.Column(db.Enum("notes", "core_cs", name="category_enum"), default="notes")
    subject = db.Column(db.String(100))
    branch = db.Column(db.String(50))
    year = db.Column(db.Integer)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)


class DSATopic(db.Model):
    __tablename__ = "dsa_topics"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    order_index = db.Column(db.Integer, default=0)


class DSAProgress(db.Model):
    __tablename__ = "dsa_progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey("dsa_topics.id"), nullable=False)
    status = db.Column(
        db.Enum("Not Started", "In Progress", "Completed", name="dsa_status_enum"),
        default="Not Started",
    )
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "topic_id", name="unique_user_topic"),)


class AptitudeQuestion(db.Model):
    __tablename__ = "aptitude_questions"

    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(
        db.Enum("A", "B", "C", "D", name="correct_option_enum"),
        nullable=False
    )
    category = db.Column(db.String(50))
    difficulty = db.Column(
        db.Enum("Easy", "Medium", "Hard", name="difficulty_enum"),
        default="Easy"
    )
    test_number = db.Column(db.Integer, default=1)          
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)


class AptitudeAttempt(db.Model):
    __tablename__ = "aptitude_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50))                     
    difficulty = db.Column(
        db.Enum("Easy", "Medium", "Hard", name="difficulty_enum")
    )                                                       
    test_number = db.Column(db.Integer)                     
    taken_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)


class InterviewQuestion(db.Model):
    __tablename__ = "interview_questions"

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    model_answer = db.Column(db.Text)
    type = db.Column(db.Enum("technical", "hr", name="interview_type_enum"), nullable=False)
    branch = db.Column(db.String(50))
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    status = db.Column(db.Enum("Pending", "Completed", name="task_status_enum"), default="Pending")
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
