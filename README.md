# Makin Damascus Bot

A Telegram bot that interfaces with Google Sheets as a database.

## Security Notice

This repository contains code for a Telegram bot that interacts with Google Sheets. To use this bot, you'll need to set up your own credentials:

1. **Telegram Bot Token**: Get this from [@BotFather](https://t.me/botfather)
2. **Google Sheets**:
   - Create a Google Cloud Project
   - Enable Google Sheets API
   - Create a Service Account
   - Download credentials as JSON
   - Share your sheet with the service account email

⚠️ **IMPORTANT**: Never commit your real credentials to the repository!

- Keep your `.env` file private
- Keep your Google service account credentials private
- Don't share your bot token or service account keys

## Setup

1. Clone this repository
2. Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

3. Set up Google Sheets credentials:
   - Rename your service account JSON file to `credentials.json`
   - Place it in the project root
   - Never commit this file!

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Run the bot:

```bash
python bot.py
```

## Deployment

For deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)

## Features

- Seamless integration with Google Sheets
- Simple API for data management
- Easy to extend functionality
- Fuzzy search capabilities
- Schema-based data handling
