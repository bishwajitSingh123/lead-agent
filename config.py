import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
LLM_MODEL = os.getenv('LLM_MODEL', 'llama-3.1-8b-instant')

# Email Configuration
EMAIL_SENDER = os.getenv('EMAIL_SENDER')  # Your Gmail address
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')  # Gmail App Password
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# File Paths
LEADS_FILE = 'data/leads.csv'
STATE_FILE = 'data/state.csv'
OUTPUT_DIR = 'outputs/drafts'

# Agent Settings
TEMPERATURE = 0.7
MAX_TOKENS = 1000