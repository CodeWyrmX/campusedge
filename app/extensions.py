from flask_sqlalchemy import SQLAlchemy

# Single shared db instance, imported by app/__init__.py and all models
db = SQLAlchemy()
