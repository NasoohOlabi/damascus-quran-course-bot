# Makin Damascus Bot Documentation

## Overview
Makin Damascus Bot is a Telegram bot designed to help manage Quran students and their progress. It integrates with Google Sheets to store and manage data efficiently.

## Features
- Student Management
- Progress Tracking
- Multiple Sheet Management
- Data Validation
- Real-time Updates

## Prerequisites
1. Telegram Bot Token (from @BotFather)
2. Google Cloud Project with Sheets API enabled
3. Google Service Account credentials
4. Python 3.7+

## Installation

### Local Setup
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

## Bot Commands

### Available Commands
- `/start` - Initialize bot and select/create sheet
- `/help` - Display help message with available commands
- `/sheets` - List all available sheets
- `/columns` - Show columns in current sheet
- `/students` - Access student management menu
- `/progress` - Track student progress

## Command Flows

### Student Management Flow
1. `/students` command
2. Options presented:
   - Add New Student
   - List Students
3. Add New Student flow:
   - Enter student name
   - Enter age
   - Select teacher
   - Set status
   - Confirm details
4. List Students shows:
   - Student name
   - Assigned teacher
   - Current status

### Progress Tracking Flow
1. `/progress` command
2. Options presented:
   - Add Progress Note
   - View Progress
3. Add Progress flow:
   - Select student
   - Enter notes
   - Add pages covered
   - Add Sura name
   - Set date
4. View Progress shows:
   - Student name
   - Progress notes
   - Pages/Sura covered
   - Date of entry

## Use Cases

### Case 1: New Student Registration
1. Teacher uses `/students` command
2. Selects "Add New Student"
3. Enters student details
4. System creates record in Google Sheets
5. Confirmation message sent

### Case 2: Daily Progress Update
1. Teacher uses `/progress` command
2. Selects "Add Progress Note"
3. Chooses student from list
4. Enters daily progress
5. System updates progress sheet

### Case 3: Progress Review
1. Teacher uses `/progress` command
2. Selects "View Progress"
3. Views chronological progress notes
4. Can track student's advancement

## Data Structure

### Students Sheet
Columns:
- name
- age
- teacher
- status
- join_date
- created
- created_by
- last_modified
- last_modified_by

### Progress Sheet
Columns:
- student_name
- notes
- pages
- sura
- date

## Best Practices
1. Regular Progress Updates
   - Update student progress daily
   - Include specific details in notes

2. Student Management
   - Keep student status updated
   - Regularly review inactive students

3. Data Validation
   - Use provided options for status fields
   - Ensure correct date formats

## Troubleshooting

### Common Issues
1. Bot Not Responding
   - Check internet connection
   - Verify bot token is correct
   - Ensure bot is running

2. Sheet Access Issues
   - Verify credentials.json is present
   - Check service account permissions
   - Ensure sheet is shared with service account

3. Data Entry Errors
   - Follow correct data formats
   - Check validation rules
   - Use suggested options when available

## Security Considerations
1. Never share bot token
2. Keep credentials.json secure
3. Regularly rotate access tokens
4. Monitor API usage
5. Restrict sheet access appropriately

## Support
For issues and feature requests, please create an issue in the repository.

## Contributing
Contributions are welcome! Please read the contributing guidelines before submitting pull requests.