from memory.memory_store import fraud_memory

class DecisionAgent:
    def assess_ring(self, ring):
        ring_id = ring["ring_id"]
        size = ring["ring_size"]
        job_ids = ring.get("job_ids", [])
        
        # Convert job_ids to strings to prevent TypeError
        job_ids_str = [str(job_id) for job_id in job_ids]
        
        # Check memory for repeat offenders
        past_scams = fraud_memory.search(ring_id) if hasattr(fraud_memory, 'search') else []
        is_repeat = len(past_scams) > 0
        
        # Decision Logic
        if is_repeat:
            severity = "CRITICAL"
            action = "IMMEDIATE ESCALATION - Platform-wide block"
        elif size >= 4:
            severity = "HIGH"
            action = "Platform-wide alert + user notifications"
        elif size >= 2:
            severity = "MEDIUM" 
            action = "Targeted monitoring + user warnings"
        else:
            severity = "LOW"
            action = "Log and monitor for patterns"
        
        # FIXED explanation generation
        explanation = self._generate_explanation(ring_id, size, job_ids_str, severity, is_repeat)
        
        # Save to memory
        fraud_memory.add(text=ring_id, meta={"severity": severity, "size": size})
        
        return {
            "ring_id": ring_id,
            "severity": severity,
            "action": action,
            "ring_size": size,
            "job_ids": job_ids_str,  # Return strings
            "is_repeat_offender": is_repeat,
            "explanation": explanation
        }
    
    def _generate_explanation(self, ring_id, size, job_ids, severity, is_repeat):
        reasons = []
        
        # Size-based reasoning
        if size >= 4:
            reasons.append(f"Multiple jobs ({size}) detected in coordinated attack pattern")
        elif size >= 2:
            reasons.append(f"Small fraud ring confirmed ({size} similar jobs)")
        else:
            reasons.append(f"Isolated suspicious job detected")
        
        # Repeat offender
        if is_repeat:
            reasons.append("Known fraud network - previously detected")
        else:
            reasons.append("New fraud pattern identified")
        
        # Action justification
        if severity in ["HIGH", "CRITICAL"]:
            reasons.append("Requires immediate platform intervention to protect users")
        elif severity == "MEDIUM":
            reasons.append("Requires close monitoring - potential for expansion")
        else:
            reasons.append("Low immediate risk but valuable for pattern recognition")
        
        # FIXED: Convert job_ids to strings before join
        job_list = ", ".join(job_ids[:3])
        if len(job_ids) > 3:
            job_list += f"... (+{len(job_ids)-3} more)"
        reasons.append(f"Affected jobs: {job_list}")
        
        return reasons
