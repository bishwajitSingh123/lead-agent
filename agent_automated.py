import os
from dotenv import load_dotenv
from groq import Groq
import logging
import time
import sys
import schedule
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
        pass

logger = logging.getLogger(__name__)

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise RuntimeError("GROQ_API_KEY missing in .env")

client = Groq(api_key=API_KEY)

# Auto-send configuration
AUTO_SEND_EMAILS = os.getenv("AUTO_SEND_EMAILS", "false").lower() == "true"
AUTO_APPROVE_THRESHOLD = os.getenv("AUTO_APPROVE_THRESHOLD", "Hot")  # Hot, Warm, Cold

# Human-in-loop configuration
EMAIL_BATCH_SIZE = int(os.getenv("EMAIL_BATCH_SIZE", "2"))  # Stop after 2 emails
emails_sent_in_session = 0

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
                time.sleep(2 ** attempt)
        
        return None
    
    def classify_lead(self, lead):
        prompt = get_classification_prompt(lead)
        response = self.call_llm(prompt)
        
        if response:
            classification = parse_json_response(response)
            if classification:
                logger.info(f"✓ Lead classified: {classification.get('category', 'Unknown')}")
                return classification
        
        logger.warning("⚠ Using fallback classification")
        return {
            "category": "Warm",
            "intent": "Unknown",
            "urgency": "Unknown",
            "concerns": [],
            "next_action": "Manual review needed",
            "reasoning": "Automated classification failed",
        }
    
    def generate_followup(self, lead, classification):
        prompt = get_followup_prompt(lead, classification)
        response = self.call_llm(prompt)
        return response if response else "Error: Could not generate email"
    
    def process_lead(self, lead):
        logger.info(f"Processing lead: {lead['name']} ({lead['email']})")
        
        classification = self.classify_lead(lead)
        draft_email = self.generate_followup(lead, classification)
        
        return {
            "lead": lead,
            "classification": classification,
            "draft": draft_email,
        }

# ----------------------------- 
# Automated Processing
# ----------------------------- 
def auto_process_leads():
    """Process leads automatically with human-in-loop control"""
    global emails_sent_in_session
    
    logger.info("=" * 70)
    logger.info("Starting automated lead processing")
    logger.info(f"Human-in-loop: Stop after {EMAIL_BATCH_SIZE} emails")
    logger.info("=" * 70)
    
    agent = LeadQualificationAgent()
    leads = load_leads()
    
    if leads.empty:
        logger.warning("No leads found in leads.csv")
        return
    
    state = load_state()
    processed_ids = set(state["lead_id"].values) if not state.empty else set()
    new_leads = leads[~leads["lead_id"].isin(processed_ids)]
    
    if new_leads.empty:
        logger.info("All leads already processed")
        return
    
    logger.info(f"Processing {len(new_leads)} new leads")
    
    for idx, lead in new_leads.iterrows():
        try:
            result = agent.process_lead(lead)
            
            # Save draft
            save_draft(lead["lead_id"], lead["name"], result["draft"])
            
            # Auto-send logic
            category = result["classification"]["category"]
            send_email_flag = False
            
            if AUTO_SEND_EMAILS:
                # Send based on threshold
                if AUTO_APPROVE_THRESHOLD == "Hot" and category == "Hot":
                    send_email_flag = True
                elif AUTO_APPROVE_THRESHOLD == "Warm" and category in ["Hot", "Warm"]:
                    send_email_flag = True
                elif AUTO_APPROVE_THRESHOLD == "Cold":
                    send_email_flag = True
            
            if send_email_flag:
                subject, body = parse_email_content(result["draft"])
                email_sent = send_email(
                    to_email=lead["email"],
                    subject=subject,
                    body=body,
                    lead_id=lead["lead_id"]
                )
                
                if email_sent:
                    emails_sent_in_session += 1
                    logger.info(f"📧 Email sent ({emails_sent_in_session}/{EMAIL_BATCH_SIZE})")
                    
                    # Human-in-loop: Stop after batch size
                    if emails_sent_in_session >= EMAIL_BATCH_SIZE:
                        logger.info("=" * 70)
                        logger.info(f"⏸️ BATCH LIMIT REACHED: {EMAIL_BATCH_SIZE} emails sent")
                        logger.info("Pausing for human review. Restart to continue.")
                        logger.info("=" * 70)
                        update_lead_state(
                            lead["lead_id"],
                            status="approved_sent",
                            next_action=result["classification"]["next_action"],
                        )
                        # Exit to require manual restart
                        sys.exit(0)
                
                status = "approved_sent" if email_sent else "approved"
            else:
                status = "approved"
                logger.info(f"Draft saved only (category: {category}, threshold: {AUTO_APPROVE_THRESHOLD})")
            
            update_lead_state(
                lead["lead_id"],
                status=status,
                next_action=result["classification"]["next_action"],
            )
            
            logger.info(f"✅ Lead {lead['lead_id']} processed (status: {status})")
        
        except Exception as e:
            logger.error(f"Error processing lead {lead['lead_id']}: {e}", exc_info=True)
    
    logger.info("=" * 70)
    logger.info("Automated processing complete")
    logger.info("=" * 70)

# ----------------------------- 
# Scheduler
# ----------------------------- 
def run_scheduled():
    """Run agent on schedule"""
    logger.info("Starting scheduled mode...")
    logger.info(f"Auto-send enabled: {AUTO_SEND_EMAILS}")
    logger.info(f"Auto-approve threshold: {AUTO_APPROVE_THRESHOLD}")
    logger.info(f"Batch size (human-in-loop): {EMAIL_BATCH_SIZE}")
    
    # Run immediately on startup
    auto_process_leads()
    
    # Schedule for every hour
    schedule.every(1).hours.do(auto_process_leads)
    
    logger.info("Scheduler started - checking for new leads every hour")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# ----------------------------- 
# Entry point
# ----------------------------- 
if __name__ == "__main__":
    mode = os.getenv("RUN_MODE", "manual")
    
    if mode == "scheduled":
        # For deployment - runs automatically
        run_scheduled()
    else:
        # For local testing - run once
        auto_process_leads()