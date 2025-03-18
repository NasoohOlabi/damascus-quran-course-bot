# Deployment Guide

This guide explains how to safely deploy the Makin Damascus Bot.

## Prerequisites

Before deploying, ensure you have:

1. Your Telegram Bot Token
2. Your Google Sheet ID
3. Your Google Service Account credentials file (`credentials.json`)

⚠️ **SECURITY WARNING**: Never commit these credentials to your repository!

## Deployment Options

### 1. Render.com (Recommended)

1. Fork this repository to your private GitHub account
2. Sign up at [render.com](https://render.com)
3. Create a new Web Service
4. Connect to your private repository
5. Configure the service:
   - Environment: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`
6. Add environment variables:

   ```
   TELEGRAM_BOT_TOKEN=your_bot_token
   GOOGLE_SHEET_ID=your_sheet_id
   ```

7. Upload `credentials.json` in the Files section

### 2. Railway.app

Similar process to Render, but use Railway's CLI for credential management.

### 3. Local Server/VPS

If deploying to your own server:

1. Clone your private repository
2. Create `.env` file with credentials
3. Place `credentials.json` in the project root
4. Run with Docker:

   ```bash
   docker build -t makin-damascus-bot .
   docker run -d \
     -e TELEGRAM_BOT_TOKEN=your_token \
     -e GOOGLE_SHEET_ID=your_sheet_id \
     -v /path/to/credentials.json:/app/credentials.json \
     makin-damascus-bot
   ```

## Security Best Practices

1. Always use a private repository
2. Never commit credentials
3. Use environment variables for sensitive data
4. Keep your `credentials.json` secure
5. Regularly rotate credentials
6. Monitor your bot's usage
7. Use secure HTTPS endpoints

## Monitoring

Once deployed, monitor your bot:

1. Check Telegram's bot status
2. Monitor Google Cloud Console for API usage
3. Check your deployment platform's logs
4. Set up alerts for errors or unusual activity
