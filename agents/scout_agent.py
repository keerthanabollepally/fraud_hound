import pandas as pd
from llm_utils import llm_risk_analysis

class ScoutAgent:
    def calculate_risk_score(self, row):
        message = str(row.get("description", ""))
        result = llm_risk_analysis(message)
        
        # FORCE FLOAT (no more TypeError)
        try:
            score = float(result.get("risk_score", 0.0))
        except:
            score = 0.0
            
        return score, result.get("reasons", []), result.get("suggestion", "")

    def scan_jobs(self, csv_path=None, df=None, threshold=0.4):
        if df is None:
            df = pd.read_csv(csv_path)

        results = []
        for idx, row in df.iterrows():
            score, reasons, suggestion = self.calculate_risk_score(row)
            
            if score >= threshold:
                results.append({
                    "job_id": row.get("job_id", idx),
                    "job_title": row.get("job_title", "Unknown"),
                    "platform": row.get("platform", "Unknown"),
                    "description": row.get("description", ""),
                    "risk_score": round(score, 2),
                    "reasons": reasons,
                    "suggestion": suggestion
                })
        return pd.DataFrame(results)
