import os
import logging
import random
from flask import current_app
from app.models.models import ContentTemplate
from datetime import datetime

logger = logging.getLogger(__name__)

# Default templates to use if none are available in the database
DEFAULT_TEMPLATES = {
    'caption': [
        "Looking for motivation? Here's your daily reminder that consistency is key to achieving your goals. #motivation #success",
        "The only limit to your growth is your mindset. Challenge yourself today. #growth #mindset",
        "Small steps forward each day lead to massive progress over time. Keep going! #progress #journey",
    ],
    'hashtags': [
        "#motivation #success #growth #mindset #inspiration",
        "#goals #achievement #progress #consistency #focus",
        "#inspiration #journey #growth #success #mindset"
    ]
}

def generate_caption_with_local_model(template_prompt, content_type):
    """
    Generate content using a locally hosted model
    This uses the transformers library for inference
    """
    try:
        from transformers import pipeline

        # Load the model - adjust model_name based on your requirements
        model_name = current_app.config.get('CONTENT_GENERATION_MODEL', 'gpt-neo-125M')
        
        # Initialize the text generation pipeline
        generator = pipeline('text-generation', model=model_name)
        
        # Generate text based on the prompt
        generated_text = generator(
            template_prompt, 
            max_length=150 if content_type == 'caption' else 50,
            num_return_sequences=1,
            temperature=0.7,
            top_k=50,
            top_p=0.95
        )
        
        # Extract the generated text from the model output
        return generated_text[0]['generated_text'].replace(template_prompt, '').strip()
    
    except Exception as e:
        logger.error(f"Error generating content with local model: {str(e)}")
        return None


def generate_caption_with_azure_openai(template_prompt, content_type):
    """
    Generate content using Azure OpenAI Service
    This requires Azure OpenAI Service to be configured
    """
    try:
        # Using the Azure OpenAI Python SDK
        from openai import AzureOpenAI
        
        client = AzureOpenAI(
            api_key=current_app.config['AZURE_OPENAI_API_KEY'],  
            api_version=current_app.config['AZURE_OPENAI_API_VERSION'],
            azure_endpoint=current_app.config['AZURE_OPENAI_ENDPOINT']
        )
        
        # Prepare the prompt
        if content_type == 'caption':
            system_message = "You are a social media expert who creates engaging Instagram captions."
            max_tokens = 150
        else:  # hashtags
            system_message = "You are a social media expert who creates relevant hashtags for Instagram posts."
            max_tokens = 50
        
        # Make the API call
        response = client.chat.completions.create(
            model="gpt-4", # Adjust model based on availability
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": template_prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logger.error(f"Error generating content with Azure OpenAI: {str(e)}")
        return None


def generate_caption(content_type='caption', template_id=None):
    """
    Main function to generate content
    Uses the specified template and model to generate content
    Falls back to local options if Azure OpenAI is not available
    """
    try:
        # Get the template from the database
        if template_id:
            template = ContentTemplate.query.get(template_id)
            if template and template.content_type == content_type:
                template_prompt = template.prompt
            else:
                raise ValueError(f"Template with ID {template_id} not found or does not match content type {content_type}")
        else:
            # Get a random active template of the specified type
            template = ContentTemplate.query.filter_by(
                content_type=content_type, 
                active=True
            ).order_by(func.random()).first()
            
            if template:
                template_prompt = template.prompt
            else:
                # Fall back to default templates
                template_prompt = random.choice(DEFAULT_TEMPLATES.get(content_type, ["Create engaging content for Instagram"]))
        
        # Add date and other context to the prompt
        current_date = datetime.now().strftime("%B %d, %Y")
        template_prompt = f"Date: {current_date}\nPrompt: {template_prompt}"
        
        # Try Azure OpenAI first if configured
        if all(key in current_app.config for key in ['AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_API_VERSION']):
            generated_content = generate_caption_with_azure_openai(template_prompt, content_type)
            if generated_content:
                return generated_content
        
        # Fall back to local model
        generated_content = generate_caption_with_local_model(template_prompt, content_type)
        if generated_content:
            return generated_content
        
        # If all else fails, use a default template
        return random.choice(DEFAULT_TEMPLATES.get(content_type, ["Check out this amazing content!"]))
    
    except Exception as e:
        logger.error(f"Error in generate_caption: {str(e)}")
        # Return a safe default in case of error
        return random.choice(DEFAULT_TEMPLATES.get(content_type, ["Check out this amazing content!"]))