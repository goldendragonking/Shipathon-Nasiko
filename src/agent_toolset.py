import json
import os
import asyncio
from typing import Any

class SupportToolset:
    """Customer Support toolset for Aura Electronics KB retrieval and escalation"""

    def __init__(self):
        self.escalation_log = []
        # Dynamically load your JSON file when the agent wakes up
        try:
            kb_path = os.path.join(os.path.dirname(__file__), 'knowledge_base.json')
            with open(kb_path, 'r') as f:
                self.kb = json.load(f)
        except Exception as e:
            self.kb = {"categories": []}
            print(f"CRITICAL ERROR: Could not load knowledge_base.json: {e}")

    def query_knowledge_base(self, search_term: str) -> str:
        """Search the Aura Electronics knowledge base.
        
        Args:
            search_term: A short keyword (e.g., 'AuraSync', 'refund').
        """
        try:
            # Split the search into individual words (e.g. "aurasync earbuds" -> ["aurasync", "earbuds"])
            terms = search_term.lower().split()
            results = []

            for category in self.kb.get("categories", []):
                for item in category.get("items", []):
                    # Combine question and answer into one big block of text to search
                    text_to_search = (item.get("question", "") + " " + item.get("answer", "")).lower()
                    
                    # If ANY of the search words match, grab the policy!
                    if any(word in text_to_search for word in terms):
                        result_text = f"Policy: {item['question']}\nAnswer: {item['answer']}"
                        if "steps" in item:
                            result_text += "\nSteps: " + " -> ".join(item["steps"])
                        results.append(result_text)

            if results:
                return "Found in Knowledge Base:\n\n" + "\n\n---\n\n".join(results[:3])
            else:
                return f"No info found for '{search_term}'. Escalate or ask user."
        except Exception as e:
            return f"Search failed: {str(e)}"

    def escalate_to_human(self, reason: str, context_summary: str) -> str:
        """Escalate to a human Tier 2 agent for critical issues, anger, fraud, or unresolvable problems.
        
        Args:
            reason: Why this is being escalated (e.g., 'angry customer', 'fraud', 'legal threat').
            context_summary: A summary of the issue so far.
        """
        try:
            ticket_id = f"TKT-{len(self.escalation_log) + 1000}"
            self.escalation_log.append({
                "ticket": ticket_id, 
                "reason": reason, 
                "context": context_summary
            })
            return f"ESCALATION SUCCESSFUL. Ticket ID: {ticket_id}. Tell the customer a Tier 2 specialist will contact them shortly."
        except Exception as e:
            return f"Escalation failed: {str(e)}"

    def get_tools(self) -> dict[str, Any]:
        """Returns the actual callable methods for the agent to use."""
        return {
            'query_knowledge_base': self.query_knowledge_base,
            'escalate_to_human': self.escalate_to_human,
        }
