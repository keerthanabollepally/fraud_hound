import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class PatternHunterAgent:
    def __init__(self, similarity_threshold=0.75):
        self.similarity_threshold = similarity_threshold
        try:
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
        except:
            self.model = None

    def detect_fraud_rings(self, undercover_results):
        scam_cases = [r for r in undercover_results if r["scam_detected"]]
        if not scam_cases:
            return []

        if self.model:
            return self._embedding_clusters(scam_cases)
        else:
            return self._rule_clusters(scam_cases)

    def _embedding_clusters(self, scam_cases):
        texts = [" ".join([m["message"] for m in case["conversation"]]) for case in scam_cases]
        embeddings = self.model.encode(texts)
        
        clusters = []
        used = set()
        for i in range(len(embeddings)):
            if i in used: continue
            cluster = [i]
            used.add(i)
            for j in range(i + 1, len(embeddings)):
                if j in used: continue
                sim = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
                if sim >= self.similarity_threshold:
                    cluster.append(j)
                    used.add(j)
            if len(cluster) > 0:
                clusters.append(cluster)
        
        return self._format_rings(scam_cases, clusters)

    def _rule_clusters(self, scam_cases):
        clusters = {}
        for case in scam_cases:
            text = " ".join([m["message"].lower() for m in case["conversation"]])
            key = "payment_scam" if any(x in text for x in ["pay", "fee", "upi"]) else "messaging_scam"
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(case)
        
        rings = []
        for idx, (key, cases) in enumerate(clusters.items()):
            rings.append({
                "ring_id": f"cluster_{idx}_{key}",
                "job_ids": [case["job_id"] for case in cases],
                "ring_size": len(cases)
            })
        return rings

    def _format_rings(self, scam_cases, clusters):
        rings = []
        for idx, cluster in enumerate(clusters):
            job_ids = [scam_cases[i]["job_id"] for i in cluster]
            rings.append({
                "ring_id": f"cluster_{idx}",
                "job_ids": job_ids,
                "ring_size": len(job_ids)
            })
        return rings
