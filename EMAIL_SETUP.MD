# Email Setup Guide for Lead Agent

## Quick Setup (5 minutes)

### Step 1: Get Gmail App Password

Since you want to test with `bishwajit.1804@gmail.com`, follow these steps:

1. **Enable 2-Step Verification** (if not already enabled):
   - Go to: https://myaccount.google.com/security
   - Click "2-Step Verification"
   - Follow the setup process

2. **Generate App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" for the app
   - Select "Windows Computer" for the device
   - Click "Generate"
   - **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)

### Step 2: Configure .env File

Create a `.env` file in your project root with:

```env
GROQ_API_KEY=your_groq_api_key_here
EMAIL_SENDER=bishwajit.1804@gmail.com
EMAIL_PASSWORD=abcdefghijklmnop
```

**Important**: 
- Remove spaces from the App Password (use `abcdefghijklmnop` not `abcd efgh ijkl mnop`)
- Never commit this file to GitHub

### Step 3: Test Email Sending

Run the agent and approve a lead - it will automatically send the email!

```bash
python agent.py
```

## Testing the Email Feature

### Option 1: Send to Your Own Email
Set up a test lead in `data/leads.csv`:

```csv
lead_id,name,email,message,source,timestamp
TEST001,Test Lead,bishwajit.1804@gmail.com,Testing the email system,Website,2026-02-09 10:00:00
```

### Option 2: Add Email Sending Step

The current agent saves drafts. To enable auto-sending, we can add an option in the human review step.

## Troubleshooting

### Error: "SMTP Authentication Failed"
- ✓ Check you're using App Password, not regular password
- ✓ Ensure 2-Step Verification is enabled
- ✓ Remove all spaces from App Password

### Error: "Less secure app access"
- Gmail no longer supports this - MUST use App Password

### Emails going to spam?
- This is normal for new sender addresses
- Add your own email to contacts to prevent this
- For production, use a dedicated email service (SendGrid, etc.)

## Production Recommendations

For real business use:
1. **Use SendGrid/Mailgun** instead of Gmail SMTP
2. **Set up SPF/DKIM records** for your domain
3. **Monitor sending limits** (Gmail: 500/day)
4. **Add unsubscribe links** for compliance

## Security Best Practices

- ✓ Never commit .env to Git (add to .gitignore)
- ✓ Rotate App Passwords every 90 days
- ✓ Use different App Passwords for different apps
- ✓ Revoke unused App Passwords immediately