from llm_utils import llm_undercover_simulation

class UndercoverAgent:
    def __init__(self):  # ← NO ARGUMENTS NEEDED
        """No chat scripts needed - uses LLM simulation"""
        pass
    
    def simulate_conversation(self, job_id, job_description=""):
        result = llm_undercover_simulation(job_description)
        return {
            "job_id": job_id,
            "scam_detected": result.get("scam_detected", False),
            "conversation": result.get("conversation", []),
            "script_id": "llm_generated" if result.get("conversation") else "rule_based"
        }
