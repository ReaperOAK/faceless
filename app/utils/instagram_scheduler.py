import os
import logging
from datetime import datetime, timedelta
from flask import current_app
from app.models.models import Post, ContentTemplate
from app.utils.content_generator import generate_caption
from app.utils.instagram_publisher import publish_to_instagram
from app import db
import random
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

def schedule_instagram_posts(scheduler):
    """
    Set up the scheduler for automated Instagram posting
    """
    # Define how often posts should be created
    post_frequency_hours = int(current_app.config.get('POST_FREQUENCY', 24))
    
    # Schedule the job to run at the specified interval
    scheduler.add_job(
        create_and_publish_post,
        'interval',
        hours=post_frequency_hours,
        id='instagram_post_job',
        replace_existing=True,
        next_run_time=datetime.now() + timedelta(minutes=1)  # First run after 1 minute
    )
    
    logger.info(f"Instagram posting scheduled every {post_frequency_hours} hours")


def create_image_with_text(text, image_path=None):
    """
    Create an image with the given text overlay
    If no image_path is provided, creates a new image with a gradient background
    """
    try:
        width, height = 1080, 1080  # Instagram square format
        
        if image_path and os.path.exists(image_path):
            # Use the existing image
            img = Image.open(image_path)
            # Resize to square format if needed
            img = img.resize((width, height))
        else:
            # Create a new image with gradient background
            img = Image.new('RGB', (width, height), color=(random.randint(0, 255), 
                                                          random.randint(0, 255), 
                                                          random.randint(0, 255)))
            
            # Add a simple gradient effect
            draw = ImageDraw.Draw(img)
            for i in range(height):
                # Create a gradient from top to bottom
                r = int((i / height) * 255)
                g = int(((height - i) / height) * 255)
                b = random.randint(0, 255)
                draw.line([(0, i), (width, i)], fill=(r, g, b, 128))
        
        # Add text overlay
        draw = ImageDraw.Draw(img)
        
        # Try to use a nice font, fall back to default if not available
        try:
            font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                    'static', 'fonts', 'roboto-bold.ttf')
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, size=40)
            else:
                font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()
        
        # Wrap text to fit the image
        wrapped_text = []
        words = text.split()
        line = ""
        for word in words:
            test_line = line + word + " "
            # Approximate text width - adjust based on your font
            if len(test_line) * 20 < width - 100:  # Leave margins
                line = test_line
            else:
                wrapped_text.append(line)
                line = word + " "
        wrapped_text.append(line)
        
        # Draw the wrapped text
        y_position = height / 2 - (len(wrapped_text) * 50 / 2)  # Center text vertically
        for line in wrapped_text:
            # Get the actual width of the line for this font
            text_width = draw.textlength(line, font=font) if hasattr(draw, 'textlength') else len(line) * 20
            
            # Center the text horizontally
            x_position = (width - text_width) / 2
            
            # Draw text with a shadow for better visibility
            draw.text((x_position+2, y_position+2), line, font=font, fill=(0, 0, 0, 200))  # Shadow
            draw.text((x_position, y_position), line, font=font, fill=(255, 255, 255, 255))  # Text
            
            y_position += 50  # Move down for the next line
        
        # Save the image
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_filename = f"generated_post_{timestamp}.jpg"
        output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the image
        img.save(output_path, format='JPEG', quality=95)
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error creating image: {str(e)}")
        return None


def create_and_publish_post():
    """
    Create a new post with AI-generated content and publish it to Instagram
    """
    try:
        logger.info("Starting automated post creation process")
        
        # Generate a caption with AI
        caption = generate_caption('caption')
        
        # Generate hashtags
        hashtags = generate_caption('hashtags')
        
        # Combine caption and hashtags
        full_caption = f"{caption}\n\n{hashtags}"
        
        # Create an image with text overlay
        image_path = create_image_with_text(caption.split("#")[0] if "#" in caption else caption)
        
        if not image_path:
            logger.error("Failed to create image for the post")
            return False
        
        # Create the post in the database
        post = Post(
            caption=full_caption,
            image_path=image_path,
            status='draft',
            scheduled_time=datetime.now()
        )
        
        db.session.add(post)
        db.session.commit()
        
        logger.info(f"Created new post with ID {post.id}")
        
        # Publish the post to Instagram
        result = publish_to_instagram(post)
        
        if result.get('success'):
            logger.info(f"Successfully published post {post.id} to Instagram")
            return True
        else:
            logger.error(f"Failed to publish post {post.id}: {result.get('error')}")
            return False
    
    except Exception as e:
        logger.error(f"Error in automated post creation: {str(e)}")
        return False