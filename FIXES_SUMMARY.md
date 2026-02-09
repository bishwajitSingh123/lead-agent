# Lead Agent - Fixes & Email Setup Summary

## Problem Fixed: Unicode Encoding Error ✓

### The Issue
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2713' in position 33
```

This happened because Windows Command Prompt uses cp1252 encoding by default, which can't display Unicode characters like ✓ (checkmark).

### The Solution

Updated the logging configuration in `agent.py`:

```python
# OLD (broken on Windows):
logging.basicConfig(
    handlers=[
        logging.FileHandler('outputs/agent.log'),
        logging.StreamHandler()
    ]
)

# NEW (works on Windows):
logging.basicConfig(
    handlers=[
        logging.FileHandler('outputs/agent.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Force UTF-8 for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass
```

---

## Email Feature Added ✓

### What's New

1. **Email sending capability** via Gmail SMTP
2. **Interactive options** during human review:
   - `[A]pprove` - Save draft only
   - `[S]end Email` - Save draft AND send email
   - `[E]dit` - Edit email, then choose to send or not
   - `[R]eject` - Reject the lead
   - `[Skip]` - Skip for now

3. **Safe email configuration** via environment variables

### Files Updated

1. **agent_with_email.py** - Enhanced version with email sending
2. **config.py** - Email SMTP configuration
3. **tools.py** - Already has `send_email()` function
4. **.env.example** - Template with email settings
5. **EMAIL_SETUP.md** - Step-by-step Gmail setup guide
6. **TESTING_GUIDE.md** - Complete testing instructions

---

## Quick Start

### Option 1: Just Fix the Unicode Error (Fastest)

Replace your current `agent.py` with the fixed version from `outputs/agent.py`.

**Changes needed**:
- Add `encoding='utf-8'` to FileHandler
- Change `logging.StreamHandler()` to `logging.StreamHandler(sys.stdout)`
- Add Windows UTF-8 reconfiguration

**Run**:
```bash
python agent.py
```

Now you can use `[A]pprove` to save drafts without errors!

---

### Option 2: Enable Email Sending (5 more minutes)

1. **Get Gmail App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Generate for "Mail" + "Windows Computer"
   - Copy the 16-character password

2. **Update .env**:
   ```env
   GROQ_API_KEY=your_existing_key
   EMAIL_SENDER=bishwajit.1804@gmail.com
   EMAIL_PASSWORD=abcdefghijklmnop  # Your app password (no spaces)
   ```

3. **Use Enhanced Agent**:
   ```bash
   copy agent_with_email.py agent.py
   python agent.py
   ```

4. **Send Test Email**:
   - Add test lead with your email address
   - Run agent
   - Choose `[S]end Email`
   - Check bishwajit.1804@gmail.com inbox!

---

## File Structure

```
lead-agent/
├── agent.py                    # ← Main script (fix this first)
├── agent_with_email.py         # ← Enhanced version with email
├── config.py                   # Email + LLM config
├── prompts.py                  # Classification + Follow-up prompts
├── tools.py                    # Load/save/email functions
├── .env                        # ← Add EMAIL_SENDER & EMAIL_PASSWORD
├── .env.example                # Template
├── data/
│   ├── leads.csv              # Input leads
│   └── lead_state.csv         # Processing state
├── outputs/
│   ├── agent.log              # Logs
│   └── drafts/                # Saved email drafts
├── EMAIL_SETUP.md             # Gmail setup guide
└── TESTING_GUIDE.md           # Step-by-step testing
```

---

## Testing Checklist

- [ ] Fix Unicode error (test with `python agent.py`)
- [ ] Save draft successfully (`[A]pprove`)
- [ ] Set up Gmail App Password
- [ ] Add email config to `.env`
- [ ] Send test email to bishwajit.1804@gmail.com
- [ ] Verify email received
- [ ] Test editing email before sending
- [ ] Clear test data before real use

---

## What Each File Does

| File | Purpose |
|------|---------|
| `agent.py` | Main orchestrator - runs the agent loop |
| `config.py` | Settings (model, email SMTP, file paths) |
| `prompts.py` | LLM prompts for classification & email generation |
| `tools.py` | Helper functions (load/save/email/parse) |
| `.env` | Secret credentials (API keys, passwords) |

---

## Common Issues & Fixes

### 1. Unicode Error Persists
**Symptom**: Still seeing UnicodeEncodeError  
**Fix**: Make sure you updated BOTH:
- `logging.FileHandler('outputs/agent.log', encoding='utf-8')`
- `logging.StreamHandler(sys.stdout)`

### 2. Email Authentication Failed
**Symptom**: SMTP error 535  
**Fix**: 
- Use App Password, not regular password
- Enable 2-Step Verification first
- Remove all spaces from App Password

### 3. Email Not Received
**Symptom**: No error, but email not in inbox  
**Fix**:
- Check spam folder
- Wait 2-3 minutes (Gmail can delay)
- Verify EMAIL_SENDER matches the account used for App Password

### 4. Invalid Option Error
**Symptom**: Typing `A` but getting "Invalid option"  
**Fix**: Make sure you're typing uppercase `A` (or just type `a` and we'll handle it)

---

## Security Reminders

🔒 **Never commit `.env` to GitHub**  
Add this to `.gitignore`:
```
.env
*.log
outputs/drafts/*
```

🔒 **Rotate App Passwords every 90 days**

🔒 **Use different App Passwords for different apps**

🔒 **Revoke unused App Passwords immediately**

---

## Next Steps

After testing successfully:

1. **Production Setup**:
   - Add real leads to `data/leads.csv`
   - Review every email before sending
   - Start with `[A]pprove` (drafts only)
   - Use `[S]end` selectively for vetted emails

2. **Scaling Up**:
   - Consider SendGrid/Mailgun for higher volume
   - Set up SPF/DKIM for better deliverability
   - Monitor Gmail's 500 emails/day limit

3. **Enhancements**:
   - Add email templates
   - Implement follow-up sequences
   - Track email opens/clicks
   - A/B test subject lines

---

## Support

If you run into issues:

1. Check `outputs/agent.log` for detailed error messages
2. Re-read `TESTING_GUIDE.md` for step-by-step help
3. Verify all environment variables are set correctly
4. Test with your own email first before real leads

---

**You're all set! The agent is ready to process leads and send emails.** 🚀