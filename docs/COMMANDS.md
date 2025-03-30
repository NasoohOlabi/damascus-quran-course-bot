# Bot Commands and Flows

## Available Commands
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