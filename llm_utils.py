import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

def safe_llm_call(prompt_func, fallback_func, *args, **kwargs):
    try:
        result = prompt_func(*args, **kwargs)
        if isinstance(result, dict) and "risk_score" in result:
            result["risk_score"] = float(result["risk_score"])
        return result
    except Exception as e:
        print(f"LLM failed: {str(e)}... Using fallback.")
        return fallback_func(*args, **kwargs)

# FIXED RISK RULES - ONLY REAL SCAMS
risk_prompt = PromptTemplate.from_template("""
Analyze ONLY for CLEAR scam indicators:
- Upfront payment demands (fee, deposit, registration)
- Off-platform redirects (WhatsApp/Telegram numbers) 
- UPI/phone payment requests

Return ONLY JSON: {{"risk_score": 0-1, "reasons": [""], "suggestion": ""}}
Message: {message}
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
        score = 0.0
        reasons = []
        
        # CRITICAL SCAM KEYWORDS ONLY (0.4+ score = flag)
        if any(word in text for word in ["pay rs", "fee rs", "deposit rs", "upi ", "+91-", "phonepe", "gpay"]):
            score += 0.5
            reasons.append("Upfront payment demand")
        if any(word in text for word in ["whatsapp ", "telegram ", "signal "]):
            score += 0.3  
            reasons.append("Off-platform redirect")
        if "registration" in text and ("fee" in text or "pay" in text):
            score += 0.2
            reasons.append("Registration fee scam")
            
        score = min(score, 1.0)
        
        return {
            "risk_score": float(score),
            "reasons": reasons or ["No clear scam indicators"],
            "suggestion": "Never pay upfront fees. Apply only through official company sites."
        }
    
    return safe_llm_call(llm_call, rule_fallback, message)

undercover_prompt = PromptTemplate.from_template("""
Simulate applicant conversation. Return ONLY JSON:
{{"conversation": [{{"sender": "applicant", "message": ""}}, {{"sender": "recruiter", "message": ""}}], "scam_detected": true/false}}
Job: {description}
""")

def llm_undercover_simulation(description):
    def llm_call(desc):
        chain = undercover_prompt | llm
        result = chain.invoke({"description": desc})
        return json.loads(result.content)
    
    def rule_fallback(desc):
        text = desc.lower()
        is_scam = any(word in text for word in ["pay", "fee", "deposit", "upi", "+91-", "whatsapp", "telegram"])
        conversation = [
            {"sender": "applicant", "message": "Hi, I'm interested in this job"},
            {"sender": "recruiter", "message": "Pay Rs500 processing fee first!" if is_scam else "Please apply through our official careers page"}
        ]
        return {"conversation": conversation, "scam_detected": is_scam}
    
    return safe_llm_call(llm_call, rule_fallback, description)
