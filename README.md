# Instagram Automation MVP

This project is an Instagram automation tool that automatically generates content and posts it to Instagram on a schedule.

## Features

- AI-powered caption generation using either local models or Azure OpenAI
- Image generation with text overlay
- Automated posting to Instagram via the Graph API
- Web interface for managing posts and content
- Scheduled posting system

## Prerequisites

1. Instagram Business Account
2. Facebook Page linked to your Instagram account
3. Facebook Developer Account with an app that has the following permissions:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`

## Installation

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables by editing the `.env` file:
   - `INSTAGRAM_USER_ID`: Your Instagram Business Account ID
   - `INSTAGRAM_ACCESS_TOKEN`: A long-lived access token for your Instagram account
   - `FACEBOOK_APP_ID`: Your Facebook App ID
   - `FACEBOOK_APP_SECRET`: Your Facebook App Secret
   
## Setup Instructions

### Converting a Personal Instagram Account to a Business Account

1. Open Instagram and go to your profile
2. Tap the menu icon in the top right corner
3. Tap Settings > Account
4. Scroll down and tap "Switch to Professional Account"
5. Select "Business" as the account type
6. Follow the prompts to connect to a Facebook Page

### Creating a Facebook Page

If you don't have a Facebook Page already:

1. Go to facebook.com and click on "Pages" in the left sidebar
2. Click "Create New Page"
3. Fill in the required information and create your page
4. Link this page to your Instagram Business Account

### Setting Up a Facebook Developer Account and App

1. Go to [developers.facebook.com](https://developers.facebook.com/)
2. Sign in or create an account
3. Create a new app by clicking "My Apps" > "Create App"
4. Select "Business" as the app type
5. Fill in the required information and create the app
6. Add the Instagram Graph API product to your app
7. Under App Review, request permissions for:
   - `instagram_basic`
   - `instagram_content_publish` 
   - `pages_read_engagement`

### Generating a Long-Lived Access Token

1. Go to the [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app from the dropdown
3. Select the permissions: `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`
4. Click "Generate Access Token" and authorize
5. This gives you a short-lived token, to get a long-lived token:
   ```bash
   curl -i -X GET "https://graph.facebook.com/v15.0/oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={app-secret}&fb_exchange_token={short-lived-token}"
   ```

## Running the Application

Start the Flask application:

```bash
python app.py
```

Access the application at http://localhost:5000

## Production Deployment

For production deployment, it's recommended to:

1. Use a production WSGI server like Gunicorn
2. Set up Azure services:
   - Azure App Service for hosting
   - Azure Key Vault for secure credential storage
   - Azure OpenAI Service for content generation
   - Azure Blob Storage for image hosting

### Azure Deployment

1. Install the Azure CLI and authenticate
2. Set up Azure services:
   ```bash
   az group create --name instagram-automation --location eastus
   az appservice plan create --name instagram-plan --resource-group instagram-automation --sku B1
   az webapp create --name your-app-name --resource-group instagram-automation --plan instagram-plan
   ```

3. Configure environment variables in Azure:
   ```bash
   az webapp config appsettings set --resource-group instagram-automation --name your-app-name --settings FLASK_ENV=production
   ```

4. Deploy the application:
   ```bash
   az webapp deployment source config-local-git --name your-app-name --resource-group instagram-automation
   git remote add azure <url-from-previous-command>
   git push azure main
   ```

## License

MIT

## Acknowledgements

- Instagram Graph API
- Flask Framework
- Hugging Face Transformers Library