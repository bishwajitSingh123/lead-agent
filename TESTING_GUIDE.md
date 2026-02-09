# Testing Guide - Lead Qualification Agent

## Quick Test (5 minutes)

### Step 1: Fix the Unicode Error

Replace your current `agent.py` with the fixed version:

**Copy from**: `agent_with_email.py` (the file with UTF-8 encoding fix)  
**To**: `agent.py`

Or just update these lines in your current `agent.py`:

```python
# Around line 22, change this:
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('outputs/agent.log', encoding='utf-8'),  # Add encoding='utf-8'
        logging.StreamHandler(sys.stdout)  # Change to sys.stdout
    ]
)

# Add right after logging setup:
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass
```

### Step 2: Test Without Email (Just Drafts)

Run the agent right now without email setup:

```bash
python agent.py
```

When you see the prompt:
```
Action? [A]pprove / [E]dit / [R]eject / [S]kip:
```

**Type**: `A` and press Enter

This will:
- ✓ Save the draft to `outputs/drafts/`
- ✓ Update the lead state
- ✓ Complete processing

**Expected Output**:
```
✅ Lead L002 approved!
```

The draft email will be saved in: `outputs/drafts/lead_L002_priya_sharma.txt`

---

## Step 3: Setup Email Testing (Optional)

### 3A. Get Gmail App Password

1. Go to: https://myaccount.google.com/apppasswords
2. Generate password for "Mail" + "Windows Computer"
3. Copy the 16-character password (remove spaces)

### 3B. Update .env File

Add these lines to your `.env`:

```env
EMAIL_SENDER=bishwajit.1804@gmail.com
EMAIL_PASSWORD=your_16_char_app_password_here
```

### 3C. Create Test Lead

Add a test lead to `data/leads.csv`:

```csv
lead_id,name,email,message,source,timestamp
TEST001,Bishwajit Test,bishwajit.1804@gmail.com,Testing the email system - please ignore,Manual Test,2026-02-09 18:00:00
```

### 3D. Use Enhanced Agent

Replace `agent.py` with `agent_with_email.py`:

```bash
# Backup current
copy agent.py agent_backup.py

# Use email version
copy agent_with_email.py agent.py

# Run it
python agent.py
```

Now you'll see a new option:
```
Action? [A]pprove / [S]end Email / [E]dit / [R]eject / [Skip]:
```

**Type**: `S` to send email immediately!

---

## Troubleshooting

### Error: UnicodeEncodeError with ✓ character
**Fix**: Use the updated `agent.py` with UTF-8 encoding (Step 1 above)

### Error: SMTP Authentication Failed
**Causes**:
1. Not using App Password (regular password won't work)
2. App Password has spaces (remove them)
3. 2-Step Verification not enabled

**Fix**: Follow Step 3A carefully

### Email sent but not received?
- Check spam folder
- Gmail may delay test emails by a few minutes
- Verify `EMAIL_SENDER` matches the Gmail account that generated the App Password

---

## What to Test

### Test 1: Draft Only (No Email)
```bash
python agent.py
# Choose [A]pprove
# ✓ Should save draft to outputs/drafts/
```

### Test 2: Send Email
```bash
python agent.py
# Choose [S]end Email
# ✓ Should send email to lead's address
# ✓ Should also save draft
```

### Test 3: Edit Email
```bash
python agent.py
# Choose [E]dit
# Paste your changes
# Type END on new line
# Choose Y to send or N to just save
```

### Test 4: Reject Lead
```bash
python agent.py
# Choose [R]eject
# Provide reason (optional)
# ✓ Lead marked as rejected in state file
```

---

## Verifying Results

### Check Draft Files
```bash
dir outputs\drafts\
# Should see: lead_L002_priya_sharma.txt
```

### Check State File
```bash
type data\lead_state.csv
# Should see processed leads with status
```

### Check Logs
```bash
type outputs\agent.log
# Should see detailed processing logs
```

### Check Email
- Go to `bishwajit.1804@gmail.com`
- Check inbox (or spam)
- Should see email from yourself with the generated follow-up

---

## Next Steps After Testing

Once everything works:

1. **Clear test data**:
   ```bash
   del data\lead_state.csv
   del /Q outputs\drafts\*
   ```

2. **Add real leads** to `data/leads.csv`

3. **Run in production mode**:
   ```bash
   python agent.py
   ```

4. **Review and approve** each lead manually

5. **Send emails** selectively using [S]end option

---

## Safety Tips

✓ Always test with your own email first  
✓ Review every email before sending  
✓ Start with [A]pprove (draft only) until confident  
✓ Keep EMAIL_PASSWORD secure (never commit to Git)  
✓ Use test leads before processing real leads