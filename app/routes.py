from flask import Blueprint, render_template, request, jsonify, current_app
import os

# Create blueprints
main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)
admin_bp = Blueprint('admin', __name__)

# Main routes for web interface
@main_bp.route('/')
def index():
    """Home page"""
    return render_template('index.html', title='Instagram Automation')

@main_bp.route('/dashboard')
def dashboard():
    """Dashboard page"""
    return render_template('dashboard.html', title='Dashboard')

# Admin routes for content management
@admin_bp.route('/')
def admin_index():
    """Admin home page"""
    return render_template('admin/index.html', title='Admin Dashboard')

@admin_bp.route('/posts')
def posts():
    """Manage posts"""
    from app.models.models import Post
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin/posts.html', title='Manage Posts', posts=posts)

@admin_bp.route('/templates')
def templates():
    """Manage content templates"""
    from app.models.models import ContentTemplate
    templates = ContentTemplate.query.all()
    return render_template('admin/templates.html', title='Content Templates', templates=templates)

@admin_bp.route('/accounts')
def accounts():
    """Manage Instagram accounts"""
    from app.models.models import InstagramAccount
    accounts = InstagramAccount.query.all()
    return render_template('admin/accounts.html', title='Instagram Accounts', accounts=accounts)

# API routes for application features
@api_bp.route('/generate-content', methods=['POST'])
def generate_content():
    """Generate content using AI"""
    from app.utils.content_generator import generate_caption
    
    content_type = request.json.get('content_type', 'caption')
    template_id = request.json.get('template_id')
    
    try:
        caption = generate_caption(content_type, template_id)
        return jsonify({'success': True, 'content': caption})
    except Exception as e:
        current_app.logger.error(f"Content generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/create-post', methods=['POST'])
def create_post():
    """Create a new post"""
    from app.models.models import Post
    from app import db
    
    data = request.json
    
    try:
        post = Post(
            caption=data.get('caption'),
            image_path=data.get('image_path'),
            scheduled_time=data.get('scheduled_time')
        )
        db.session.add(post)
        db.session.commit()
        
        return jsonify({'success': True, 'post': post.to_dict()})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Post creation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/publish-post/<int:post_id>', methods=['POST'])
def publish_post(post_id):
    """Publish a post to Instagram"""
    from app.utils.instagram_publisher import publish_to_instagram
    from app.models.models import Post
    from app import db
    
    try:
        post = Post.query.get_or_404(post_id)
        result = publish_to_instagram(post)
        
        if result.get('success'):
            post.status = 'published'
            post.instagram_id = result.get('instagram_id')
            post.published_time = datetime.utcnow()
            db.session.commit()
            
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Publishing error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500