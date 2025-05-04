import os
import requests
import logging
from datetime import datetime, timedelta
from flask import current_app
from app.models.models import Post, InstagramAccount
from app import db

logger = logging.getLogger(__name__)

def create_media_container(image_url, caption, access_token, instagram_user_id):
    """
    Step 1: Create a media container on Instagram
    Returns the creation_id of the container
    """
    api_url = f"{current_app.config['INSTAGRAM_GRAPH_API_URL']}/{instagram_user_id}/media"
    
    params = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token
    }
    
    try:
        response = requests.post(api_url, params=params)
        response_data = response.json()
        
        if 'id' in response_data:
            return {'success': True, 'creation_id': response_data['id']}
        else:
            error_message = response_data.get('error', {}).get('message', 'Unknown error')
            logger.error(f"Failed to create media container: {error_message}")
            return {'success': False, 'error': error_message}
    
    except Exception as e:
        logger.error(f"Exception when creating media container: {str(e)}")
        return {'success': False, 'error': str(e)}


def publish_media(creation_id, access_token, instagram_user_id):
    """
    Step 2: Publish the media container to Instagram
    Returns the Instagram post ID
    """
    api_url = f"{current_app.config['INSTAGRAM_GRAPH_API_URL']}/{instagram_user_id}/media_publish"
    
    params = {
        "creation_id": creation_id,
        "access_token": access_token
    }
    
    try:
        response = requests.post(api_url, params=params)
        response_data = response.json()
        
        if 'id' in response_data:
            return {'success': True, 'instagram_id': response_data['id']}
        else:
            error_message = response_data.get('error', {}).get('message', 'Unknown error')
            logger.error(f"Failed to publish media: {error_message}")
            return {'success': False, 'error': error_message}
    
    except Exception as e:
        logger.error(f"Exception when publishing media: {str(e)}")
        return {'success': False, 'error': str(e)}


def get_public_url_for_image(post):
    """
    Generate a publicly accessible URL for the image
    For production, this would use Azure Blob Storage
    For local development, we'll use a placeholder technique
    """
    if current_app.config.get('AZURE_STORAGE_CONNECTION_STRING'):
        # In production, use Azure Blob Storage
        from azure.storage.blob import BlobServiceClient, ContentSettings
        
        blob_service_client = BlobServiceClient.from_connection_string(
            current_app.config['AZURE_STORAGE_CONNECTION_STRING']
        )
        container_client = blob_service_client.get_container_client(
            current_app.config['AZURE_STORAGE_CONTAINER']
        )
        
        # Generate a unique blob name
        blob_name = f"post_{post.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.jpg"
        
        # Upload the image to Azure Blob Storage
        with open(post.image_path, "rb") as data:
            container_client.upload_blob(
                name=blob_name,
                data=data,
                content_settings=ContentSettings(content_type="image/jpeg")
            )
        
        # Get the public URL for the image
        return f"{container_client.primary_endpoint}/{blob_name}"
    else:
        # For local development: You would need to configure ngrok or a similar service
        # to expose your local files to the public internet
        # This is a placeholder - you'd need to implement a real solution
        return "https://placekitten.com/800/800"  # Placeholder image URL for testing


def refresh_long_lived_token(account):
    """
    Refresh a long-lived access token before it expires
    """
    api_url = f"{current_app.config['INSTAGRAM_GRAPH_API_URL']}/oauth/access_token"
    
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": current_app.config['FACEBOOK_APP_ID'],
        "client_secret": current_app.config['FACEBOOK_APP_SECRET'],
        "fb_exchange_token": account.access_token
    }
    
    try:
        response = requests.post(api_url, params=params)
        response_data = response.json()
        
        if 'access_token' in response_data:
            account.access_token = response_data['access_token']
            # Tokens usually valid for 60 days
            account.token_expires_at = datetime.utcnow() + timedelta(days=60)
            db.session.commit()
            return True
        else:
            logger.error(f"Failed to refresh token: {response_data}")
            return False
    
    except Exception as e:
        logger.error(f"Exception when refreshing token: {str(e)}")
        return False


def publish_to_instagram(post):
    """
    Main function to publish a post to Instagram
    Takes a Post object and handles the full publishing process
    """
    # Get an active Instagram account
    account = InstagramAccount.query.filter_by(active=True).first()
    
    if not account:
        return {'success': False, 'error': 'No active Instagram account found'}
    
    # Check if token needs refreshing
    if not account.is_token_valid():
        refresh_success = refresh_long_lived_token(account)
        if not refresh_success:
            return {'success': False, 'error': 'Failed to refresh access token'}
    
    # Get public URL for the image
    image_url = get_public_url_for_image(post)
    post.image_url = image_url
    
    # Create media container
    container_result = create_media_container(
        image_url=image_url,
        caption=post.caption,
        access_token=account.access_token,
        instagram_user_id=account.instagram_user_id
    )
    
    if not container_result['success']:
        post.status = 'failed'
        db.session.commit()
        return container_result
    
    # Store the creation_id
    post.creation_id = container_result['creation_id']
    post.status = 'pending'
    db.session.commit()
    
    # Publish the media
    publish_result = publish_media(
        creation_id=container_result['creation_id'],
        access_token=account.access_token,
        instagram_user_id=account.instagram_user_id
    )
    
    if not publish_result['success']:
        post.status = 'failed'
        db.session.commit()
        return publish_result
    
    # Update the post with Instagram ID
    post.instagram_id = publish_result['instagram_id']
    post.status = 'published'
    post.published_time = datetime.utcnow()
    db.session.commit()
    
    return {
        'success': True, 
        'instagram_id': publish_result['instagram_id'],
        'message': 'Post successfully published to Instagram'
    }