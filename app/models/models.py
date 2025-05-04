from datetime import datetime
from app import db

class Post(db.Model):
    """Model for Instagram posts"""
    id = db.Column(db.Integer, primary_key=True)
    caption = db.Column(db.String(2200), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(255))
    creation_id = db.Column(db.String(255))
    instagram_id = db.Column(db.String(255))
    status = db.Column(db.String(50), default='draft')  # draft, pending, published, failed
    scheduled_time = db.Column(db.DateTime)
    published_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Post {self.id}: {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'caption': self.caption,
            'image_path': self.image_path,
            'image_url': self.image_url,
            'instagram_id': self.instagram_id,
            'status': self.status,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'published_time': self.published_time.isoformat() if self.published_time else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class ContentTemplate(db.Model):
    """Model for content generation templates"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    content_type = db.Column(db.String(50), default='caption')  # caption, hashtags, comment
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ContentTemplate {self.id}: {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'prompt': self.prompt,
            'content_type': self.content_type,
            'active': self.active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class InstagramAccount(db.Model):
    """Model for Instagram account credentials and metadata"""
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(100), nullable=False)
    instagram_user_id = db.Column(db.String(100), nullable=False)
    access_token = db.Column(db.Text, nullable=False)
    token_expires_at = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<InstagramAccount {self.id}: {self.account_name}>'
    
    def is_token_valid(self):
        """Check if the access token is still valid"""
        if not self.token_expires_at:
            return False
        return datetime.utcnow() < self.token_expires_at