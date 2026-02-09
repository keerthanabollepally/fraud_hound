import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# LLM Setup
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)

def safe_llm_call(prompt_func, fallback_func, *args, **kwargs):
    """Production-grade LLM fallback - FLOAT GUARANTEED"""
    try:
        result = prompt_func(*args, **kwargs)
        # FLOAT SAFETY: Ensure risk_score is always float
        if isinstance(result, dict) and "risk_score" in result:
            result["risk_score"] = float(result["risk_score"])
        return result
    except Exception as e:
        print(f"LLM failed: {str(e)[:100]}... Using fallback.")
        result = fallback_func(*args, **kwargs)
        if isinstance(result, dict) and "risk_score" in result:
            result["risk_score"] = float(result["risk_score"])
        return result


risk_prompt = PromptTemplate.from_template("""
Analyze this job message for scam indicators.

Return ONLY valid JSON:
{{
  "risk_score": number_between_0_and_1,
  "reasons": ["list", "of", "3-5", "signals"],
  "suggestion": "short safety advice (1 sentence)"
}}

Message: {message}

Be precise. No explanations outside JSON.
""")

def llm_risk_analysis(message):
    def llm_call(msg):
        chain = risk_prompt | llm
        result = chain.invoke({"message": msg})
        parsed = json.loads(result.content)
        parsed["risk_score"] = float(parsed["risk_score"])
        return parsed
    
    def rule_fallback(msg):
        text = msg.lower()
        reasons = []
        
        if any(x in text for x in ["telegram", "whatsapp", "signal"]):
            reasons.append("Off-platform messaging requested")
        if any(x in text for x in ["pay", "fee", "deposit", "registration", "processing"]):
            reasons.append("Upfront payment demanded")
        if any(x in text for x in ["urgent", "today", "immediately", "now"]):
            reasons.append("High-pressure urgency tactics")
        if any(x in text for x in ["guaranteed", "100%", "easy money"]):
            reasons.append("Unrealistic earnings promises")
            
        score = 0.0
        if any(x in text for x in ["pay", "fee"]): score += 0.40
        if any(x in text for x in ["telegram", "whatsapp"]): score += 0.30
        if any(x in text for x in ["urgent", "today"]): score += 0.20
        if len(reasons) >= 3: score += 0.10
        score = min(score, 1.0)
        
        return {
            "risk_score": float(score),
            "reasons": reasons if reasons else ["No clear scam indicators"],
            "suggestion": "Never pay upfront. Verify via official company website."
        }
    
    return safe_llm_call(llm_call, rule_fallback, message)


undercover_prompt = PromptTemplate.from_template("""
You are an undercover job applicant investigating potential scams.

IMPORTANT: Generate FULL realistic conversation (applicant + recruiter responses).

Job description: {description}

Return ONLY JSON:
{{
  "conversation": [
    {{"sender": "applicant", "message": "Hi I'm interested"}},
    {{"sender": "recruiter", "message": "recruiter reply"}},
    {{"sender": "applicant", "message": "follow up"}},
    {{"sender": "recruiter", "message": "their reply"}},
    ...
  ],
  "scam_detected": true_or_false
}}

Show 5-6 message exchanges. Reveal payment requests, urgency, WhatsApp redirects.
""")

def llm_undercover_simulation(description):
    def llm_call(desc):
        chain = undercover_prompt | llm
        result = chain.invoke({"description": desc})
        return json.loads(result.content)
    
    def rule_fallback(desc):
        text = desc.lower()
        is_scam = any(x in text for x in ["pay", "fee", "deposit", "telegram", "whatsapp", "urgent"])
        
        if is_scam:
           
            conversation = [
                {"sender": "applicant", "message": "Hi, I'm interested in the data entry job"},
                {"sender": "recruiter", "message": "Congratulations! You're selected for immediate start!"},
                {"sender": "applicant", "message": "Great! What's next?"},
                {"sender": "recruiter", "message": "Please pay ₹500 processing fee via UPI to activate account"},
                {"sender": "applicant", "message": "Why payment required for data entry?"},
                {"sender": "recruiter", "message": "Standard procedure. Send to +91-9876543210 Google Pay NOW!"}
            ]
        else:
            
            conversation = [
                {"sender": "applicant", "message": "Hi, interested in Python developer role"},
                {"sender": "recruiter", "message": "Thanks for applying! Please submit resume via link"},
                {"sender": "applicant", "message": "Done, anything else?"},
                {"sender": "recruiter", "message": "Perfect. HR will contact you within 2 days. No fees required"}
            ]
        
        return {
            "conversation": conversation,
            "scam_detected": is_scam
        }
    
    return safe_llm_call(llm_call, rule_fallback, description)


def llm_decision_explanation(ring_id, size, severity, is_repeat=False):
    """Rich explanations for DecisionAgent"""
    def llm_call(data):
        prompt = f"""
        Explain fraud ring decision: {data['ring_id']} (size: {data['size']}, severity: {data['severity']})
        
        Return ONLY: {{"explanation": ["reason1", "reason2", "reason3"]}}
        """
        chain = PromptTemplate.from_template(prompt) | llm
        result = chain.invoke(data)
        return json.loads(result.content)["explanation"]
    
    def rule_fallback(data):
        reasons = [
            f" Ring size: {data['size']} confirmed scam jobs",
            f" {'Repeat offender' if data['repeat'] else 'New fraud pattern'} detected",
            f" Severity: {data['severity']} (automated cluster analysis)"
        ]
        return reasons
    
    data = {
        "ring_id": ring_id, 
        "size": size, 
        "severity": severity, 
        "repeat": is_repeat
    }
    return safe_llm_call(llm_call, rule_fallback, data)
