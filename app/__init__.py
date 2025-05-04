import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler

# Initialize extensions
db = SQLAlchemy()
scheduler = BackgroundScheduler()

def create_app(config_name='development'):
    """Factory function to create and configure the Flask application"""
    from config.config import config_by_name
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_by_name[config_name])
    
    # Set up extensions
    db.init_app(app)
    
    # Register blueprints
    from app.routes import main_bp, api_bp, admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Initialize database
    with app.app_context():
        db.create_all()
    
    # Initialize scheduler for automated posting
    if not scheduler.running:
        from app.utils.instagram_scheduler import schedule_instagram_posts
        schedule_instagram_posts(scheduler)
        scheduler.start()
    
    return app