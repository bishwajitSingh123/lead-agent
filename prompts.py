def get_classification_prompt(lead):
    """Generate classification prompt for LLM"""
    
    return f"""You are a sales assistant analyzing incoming leads.

Lead Information:
- Name: {lead['name']}
- Email: {lead['email']}
- Message: {lead['message']}
- Source: {lead['source']}

Analyze and classify this lead:

1. Category: Hot/Warm/Cold
   - Hot: Clear intent, budget indicators, urgent timeline
   - Warm: Interested but needs nurturing
   - Cold: Generic inquiry, low intent

2. Intent: What do they actually want?

3. Urgency: Immediate / This Week / This Month / Unknown

4. Key Concerns: Any objections or blockers mentioned?

5. Next Best Action: What should we do next?

Respond ONLY in this JSON format (no other text):
{{
  "category": "Hot/Warm/Cold",
  "intent": "brief description",
  "urgency": "timeline",
  "concerns": ["list", "of", "concerns"],
  "next_action": "suggested action",
  "reasoning": "why you classified this way"
}}"""


def get_followup_prompt(lead, classification):
    """Generate follow-up email prompt"""
    
    return f"""You are a professional sales assistant writing a follow-up email.

Lead Details:
- Name: {lead['name']}
- Their Message: {lead['message']}
- Classification: {classification['category']}
- Intent: {classification['intent']}
- Urgency: {classification['urgency']}

Write a personalized follow-up email that:
1. Addresses their specific inquiry directly
2. Builds credibility: "I build production-grade AI systems (medical imaging, clinical-grade pipelines)"
3. Suggests a clear next step based on urgency
4. Professional but warm and human tone
5. Keep it concise: 3-4 short paragraphs

Format your response as:
Subject: [compelling subject line]

Dear {lead['name']},

[Email body - be specific to their message]

Best regards,
Bishwajit Singh

Respond with ONLY the email (subject + body), no other text."""