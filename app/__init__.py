from flask import Flask, redirect, url_for
from config import Config
from app.extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Register blueprints
    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    from app.dashboard.routes import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from app.dsa.routes import dsa_bp
    app.register_blueprint(dsa_bp)

    from app.aptitude.routes import aptitude_bp
    app.register_blueprint(aptitude_bp)

    from app.planner.routes import planner_bp
    app.register_blueprint(planner_bp)

    from app.resources.routes import resources_bp
    app.register_blueprint(resources_bp)

    from app.interview.routes import interview_bp
    app.register_blueprint(interview_bp)

    from app.admin.routes import admin_bp
    app.register_blueprint(admin_bp)

    from app.profile.routes import profile_bp
    app.register_blueprint(profile_bp)

    # Root URL - redirect to login page instead of 404
    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    return app
