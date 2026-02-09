import pandas as pd
import json
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import LEADS_FILE, STATE_FILE, OUTPUT_DIR, EMAIL_SENDER, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT


def load_leads():
    """Load leads from CSV"""
    try:
        df = pd.read_csv(LEADS_FILE)
        print(f"✓ Loaded {len(df)} leads from {LEADS_FILE}")
        return df
    except FileNotFoundError:
        print(f"✗ Error: {LEADS_FILE} not found")
        return pd.DataFrame()
    except Exception as e:
        print(f"✗ Error loading leads: {e}")
        return pd.DataFrame()


def load_state():
    """Load lead state tracking"""
    try:
        if os.path.exists(STATE_FILE) and os.path.getsize(STATE_FILE) > 0:
            return pd.read_csv(STATE_FILE)
        else:
            # Create new state file
            df = pd.DataFrame(columns=['lead_id', 'status', 'follow_up_count', 
                                      'last_contact', 'next_action'])
            df.to_csv(STATE_FILE, index=False)
            return df
    except Exception as e:
        print(f"⚠ Warning: Could not load state file: {e}")
        return pd.DataFrame(columns=['lead_id', 'status', 'follow_up_count', 
                                    'last_contact', 'next_action'])


def update_lead_state(lead_id, status, next_action):
    """Update lead state after processing"""
    state = load_state()
    
    # Check if lead exists in state
    if lead_id in state['lead_id'].values:
        # Update existing
        state.loc[state['lead_id'] == lead_id, 'status'] = status
        state.loc[state['lead_id'] == lead_id, 'follow_up_count'] += 1
        state.loc[state['lead_id'] == lead_id, 'last_contact'] = datetime.now()
        state.loc[state['lead_id'] == lead_id, 'next_action'] = next_action
    else:
        # Add new
        new_row = pd.DataFrame([{
            'lead_id': lead_id,
            'status': status,
            'follow_up_count': 1,
            'last_contact': datetime.now(),
            'next_action': next_action
        }])
        state = pd.concat([state, new_row], ignore_index=True)
    
    state.to_csv(STATE_FILE, index=False)
    print(f"✓ State updated for lead {lead_id}")


def save_draft(lead_id, lead_name, draft_email):
    """Save approved email draft"""
    filename = f"{OUTPUT_DIR}/lead_{lead_id}_{lead_name.replace(' ', '_').lower()}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(draft_email)
    
    print(f"✓ Draft saved: {filename}")
    return filename


def parse_json_response(response_text):
    """Safely parse LLM JSON response"""
    try:
        # Try to extract JSON from response
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        
        if start != -1 and end > start:
            json_str = response_text[start:end]
            return json.loads(json_str)
        else:
            print("⚠ Warning: No JSON found in response")
            return None
    except json.JSONDecodeError as e:
        print(f"⚠ Warning: Could not parse JSON: {e}")
        return None


def send_email(to_email, subject, body, lead_id):
    """
    Send email via SMTP (Gmail)
    Returns: True if sent successfully, False otherwise
    """
    try:
        # Validate email config
        if not EMAIL_SENDER or not EMAIL_PASSWORD:
            print("❌ Email credentials not configured in .env")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_SENDER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Attach body
        msg.attach(MIMEText(body, 'plain'))
        
        # Send via SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure connection
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email sent to {to_email} (Lead {lead_id})")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Email authentication failed. Check EMAIL_PASSWORD (use App Password for Gmail)")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


def parse_email_content(draft_email):
    """
    Extract subject and body from generated email
    Returns: (subject, body) tuple
    """
    lines = draft_email.strip().split('\n')
    
    subject = "Follow-up on your inquiry"  # Default
    body_lines = []
    
    found_subject = False
    for line in lines:
        if line.startswith('Subject:'):
            subject = line.replace('Subject:', '').strip()
            found_subject = True
        elif found_subject or not line.startswith('Subject:'):
            body_lines.append(line)
    
    body = '\n'.join(body_lines).strip()
    
    return subject, body