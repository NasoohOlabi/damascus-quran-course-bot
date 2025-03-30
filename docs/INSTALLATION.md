# Installation Guide

## Prerequisites
1. Telegram Bot Token (from @BotFather)
2. Google Cloud Project with Sheets API enabled
3. Google Service Account credentials
4. Python 3.7+

## Local Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd makin-damascus-bot
   ```

2. Create and activate virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Add your Telegram Bot Token
   - Set Google Sheets credentials path

5. Place Google Sheets credentials:
   - Rename your service account JSON to `credentials.json`
   - Place it in the project root

## Security Best Practices
1. Never commit credentials to the repository
2. Keep your `.env` file private
3. Keep your Google service account credentials private
4. Don't share your bot token or service account keys

## Troubleshooting

### Common Issues
1. **Bot not responding**
   - Check if bot token is correct
   - Ensure bot is running
   - Check internet connection

2. **Google Sheets errors**
   - Verify credentials.json is present
   - Check if service account has access
   - Ensure Sheets API is enabled

3. **Environment issues**
   - Confirm Python version compatibility
   - Check if all dependencies are installed
   - Verify environment variables are set