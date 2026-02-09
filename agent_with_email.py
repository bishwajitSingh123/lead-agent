import os
from dotenv import load_dotenv
from groq import Groq
import logging
import time
import sys

from config import LLM_MODEL, TEMPERATURE, MAX_TOKENS
from prompts import get_classification_prompt, get_followup_prompt
from tools import (
    load_leads,
    load_state,
    update_lead_state,
    save_draft,
    parse_json_response,
    send_email,
    parse_email_content,
)

# -----------------------------
# Setup
# -----------------------------
load_dotenv()

# Logging Configuration with UTF-8 support
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
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
        pass  # Fallback if reconfigure not available

logger = logging.getLogger(__name__)

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise RuntimeError("GROQ_API_KEY missing in .env")

client = Groq(api_key=API_KEY)


# -----------------------------
# Agent
# -----------------------------
class LeadQualificationAgent:
    """Main agent for lead qualification and follow-up"""

    def __init__(self):
        self.model = LLM_MODEL
        self.temperature = TEMPERATURE
        self.max_tokens = MAX_TOKENS

    def call_llm(self, prompt):
        """Groq LLM call wrapper with retries"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful sales assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )

                if not response or not response.choices:
                    raise ValueError("Empty response")

                logger.info(f"✓ LLM response received (attempt {attempt+1})")
                return response.choices[0].message.content

            except Exception as e:
                logger.error(f"LLM Error (attempt {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None

    # -------------------------

    def classify_lead(self, lead):
        prompt = get_classification_prompt(lead)
        response = self.call_llm(prompt)

        if response:
            classification = parse_json_response(response)
            if classification:
                logger.info(f"✓ Lead classified: {classification.get('category', 'Unknown')}")
                return classification

        # fallback
        logger.warning("⚠ Using fallback classification")
        return {
            "category": "Warm",
            "intent": "Unknown",
            "urgency": "Unknown",
            "concerns": [],
            "next_action": "Manual review needed",
            "reasoning": "Automated classification failed",
        }

    # -------------------------

    def generate_followup(self, lead, classification):
        prompt = get_followup_prompt(lead, classification)
        response = self.call_llm(prompt)
        return response if response else "Error: Could not generate email"

    # -------------------------

    def process_lead(self, lead):
        print(f"\n{'='*70}")
        print(f"Processing Lead: {lead['name']} ({lead['email']})")
        print(f"Source: {lead['source']}")
        print(f"Message: {lead['message'][:100]}...")
        logger.info(f"Processing lead_id: {lead['lead_id']}")

        print("\n🤖 Analyzing lead...")
        classification = self.classify_lead(lead)

        print("📧 Generating follow-up email...")
        draft_email = self.generate_followup(lead, classification)

        return {
            "lead": lead,
            "classification": classification,
            "draft": draft_email,
        }


# -----------------------------
# Human Review with Email Option
# -----------------------------
def human_review(result):
    print(f"\n{'='*70}")
    print("📊 CLASSIFICATION RESULTS")
    print(f"{'='*70}")
    print(f"Category: {result['classification']['category']}")
    print(f"Intent: {result['classification']['intent']}")
    print(f"Urgency: {result['classification']['urgency']}")
    print(f"Next Action: {result['classification']['next_action']}")
    print(f"\nReasoning: {result['classification']['reasoning']}")

    print(f"\n{'='*70}")
    print("📧 DRAFT EMAIL")
    print(f"{'='*70}")
    print(result["draft"])
    print(f"{'='*70}\n")

    while True:
        action = input("Action? [A]pprove / [S]end Email / [E]dit / [R]eject / [Skip]: ").strip().upper()

        if action == "A":
            logger.info("Lead approved - draft saved only")
            return "approve", result["draft"], False

        elif action == "S":
            logger.info("Lead approved - will send email")
            return "approve", result["draft"], True

        elif action == "E":
            print("\nPaste edited email (type 'END' on a new line):")
            lines = []
            while True:
                line = input()
                if line == "END":
                    break
                lines.append(line)
            edited_draft = "\n".join(lines)
            
            send_choice = input("Send this edited email? [Y/N]: ").strip().upper()
            send_now = (send_choice == "Y")
            
            logger.info(f"Lead approved with edits - send={send_now}")
            return "approve", edited_draft, send_now

        elif action == "R":
            reason = input("Rejection reason (optional): ")
            logger.info(f"Lead rejected: {reason}")
            return "reject", reason, False

        elif action == "SKIP":
            logger.info("Lead skipped")
            return "skip", None, False

        else:
            print("Invalid option. Choose A/S/E/R/Skip")


# -----------------------------
# Validation
# -----------------------------
def validate_setup():
    """Validate environment before running"""
    issues = []
    
    if not os.getenv("GROQ_API_KEY"):
        issues.append("❌ GROQ_API_KEY not found in .env")
    
    if not os.path.exists('data/leads.csv'):
        issues.append("❌ data/leads.csv missing")
    
    # Check email config (warning only)
    if not os.getenv("EMAIL_SENDER") or not os.getenv("EMAIL_PASSWORD"):
        print("⚠️  Warning: Email not configured (EMAIL_SENDER/EMAIL_PASSWORD missing)")
        print("   You can still save drafts, but cannot send emails automatically.")
        print("   See EMAIL_SETUP.md for configuration instructions.\n")
    
    if not os.path.exists('outputs'):
        os.makedirs('outputs/drafts', exist_ok=True)
        logger.info("✓ Created outputs directory")
    
    if not os.path.exists('data'):
        os.makedirs('data', exist_ok=True)
        logger.info("✓ Created data directory")
    
    if issues:
        for issue in issues:
            print(issue)
        return False
    
    print("✓ All validations passed!")
    return True


# -----------------------------
# Main
# -----------------------------
def main():
    print("\n" + "=" * 70)
    print("🚀 LEAD QUALIFICATION & FOLLOW-UP AGENT (Groq)")
    print("=" * 70 + "\n")
    logger.info("Agent started")

    agent = LeadQualificationAgent()

    leads = load_leads()
    if leads.empty:
        print("✗ No leads found.")
        logger.warning("No leads found in leads.csv")
        return

    state = load_state()
    processed_ids = set(state["lead_id"].values) if not state.empty else set()

    new_leads = leads[~leads["lead_id"].isin(processed_ids)]

    if new_leads.empty:
        print("✓ All leads already processed!")
        logger.info("All leads already processed")
        return

    print(f"Found {len(new_leads)} new leads.\n")
    logger.info(f"Processing {len(new_leads)} new leads")

    for idx, lead in new_leads.iterrows():
        try:
            result = agent.process_lead(lead)

            action, content, send_email_flag = human_review(result)

            if action == "approve":
                # Always save draft
                save_draft(lead["lead_id"], lead["name"], content)
                
                # Send email if requested
                if send_email_flag:
                    subject, body = parse_email_content(content)
                    email_sent = send_email(
                        to_email=lead["email"],
                        subject=subject,
                        body=body,
                        lead_id=lead["lead_id"]
                    )
                    
                    if email_sent:
                        print(f"\n✅ Email sent to {lead['email']}!")
                        status = "approved_sent"
                    else:
                        print(f"\n⚠️  Draft saved but email failed to send")
                        status = "approved"
                else:
                    print(f"\n✅ Draft saved (email not sent)")
                    status = "approved"
                
                update_lead_state(
                    lead["lead_id"],
                    status=status,
                    next_action=result["classification"]["next_action"],
                )
                print(f"✅ Lead {lead['lead_id']} processed!\n")

            elif action == "reject":
                update_lead_state(
                    lead["lead_id"], status="rejected", next_action="no_action"
                )
                print(f"\n❌ Lead {lead['lead_id']} rejected.\n")

            elif action == "skip":
                print(f"\n⏭️ Lead {lead['lead_id']} skipped.\n")

        except Exception as e:
            logger.error(f"Error processing lead {lead['lead_id']}: {e}", exc_info=True)
            print(f"\n✗ Error processing lead {lead['lead_id']}: {e}\n")

    print("\n" + "=" * 70)
    print("✅ PROCESSING COMPLETE!")
    print("=" * 70 + "\n")
    logger.info("Agent finished successfully")


if __name__ == "__main__":
    if not validate_setup():
        sys.exit(1)
    main()