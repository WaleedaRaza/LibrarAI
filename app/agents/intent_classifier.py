"""
Alexandria Library - Intent Classifier Agent

PURPOSE: Map user input → conceptual domain
FORBIDDEN: answers, book selection, analysis

This agent determines WHAT domain to look in.
It does NOT select books or chapters.
It does NOT answer questions.
"""

from ..config import settings
from .contracts import IntentResult, VALID_DOMAINS, validate_domain
from .llm_provider import get_llm_provider


class IntentClassifier:
    """
    Classifies user questions into domains.
    
    Stateless. Pure. Replaceable.
    """
    
    def classify(self, question: str) -> IntentResult:
        """
        Classify a question into a domain.
        
        Returns IntentResult with domain and subdomain.
        Returns is_valid=False if we can't or shouldn't route.
        """
        if settings.USE_MOCK_AGENTS:
            return self._mock_classify(question)
        return self._llm_classify(question)
    
    def _mock_classify(self, question: str) -> IntentResult:
        """
        Mock classifier for development.
        Uses keyword matching to simulate classification.
        """
        question_lower = question.lower()
        
        # Simple keyword-based classification
        if any(word in question_lower for word in ["stoic", "marcus aurelius", "meditations", "virtue", "ethics", "philosophy", "meaning", "death", "suffering"]):
            return IntentResult(
                domain="Philosophy",
                subdomain="Stoicism",
                confidence=0.85
            )
        
        if any(word in question_lower for word in ["war", "strategy", "sun tzu", "conflict", "battle", "military", "enemy", "tactics"]):
            return IntentResult(
                domain="Strategy",
                subdomain="Military Strategy",
                confidence=0.85
            )
        
        if any(word in question_lower for word in ["power", "machiavelli", "prince", "politics", "leadership", "influence", "manipulation"]):
            return IntentResult(
                domain="Strategy",
                subdomain="Political Philosophy",
                confidence=0.80
            )
        
        if any(word in question_lower for word in ["code", "software", "programming", "system", "architecture", "engineering", "database"]):
            return IntentResult(
                domain="Technology",
                subdomain="Software Engineering",
                confidence=0.85
            )
        
        if any(word in question_lower for word in ["security", "hacking", "cryptography", "vulnerability", "threat"]):
            return IntentResult(
                domain="Technology",
                subdomain="Security",
                confidence=0.85
            )
        
        if any(word in question_lower for word in ["mind", "psychology", "bias", "decision", "thinking", "cognitive", "behavior"]):
            return IntentResult(
                domain="Psychology",
                subdomain="Cognitive Science",
                confidence=0.80
            )
        
        if any(word in question_lower for word in ["business", "management", "startup", "company", "entrepreneur"]):
            return IntentResult(
                domain="Business",
                subdomain="Management",
                confidence=0.75
            )
        
        if any(word in question_lower for word in ["economics", "market", "money", "capitalism", "trade"]):
            return IntentResult(
                domain="Economics",
                subdomain=None,
                confidence=0.75
            )
        
        # Default: Philosophy (broadest domain)
        return IntentResult(
            domain="Philosophy",
            subdomain=None,
            confidence=0.50
        )
    
    def _llm_classify(self, question: str) -> IntentResult:
        """
        Real LLM classification with structured output.
        
        Returns:
            IntentResult with validated domain, or refusal if unclassifiable
        """
        try:
            provider = get_llm_provider()
            
            system_prompt = f"""You are a librarian who classifies questions into knowledge domains.

Available domains: {', '.join(VALID_DOMAINS)}

Analyze the user's question and determine which domain it belongs to.

RESPOND WITH ONLY VALID JSON:
{{
  "domain": "...",
  "subdomain": "...",
  "confidence": 0.0-1.0
}}

OR if the question is inappropriate, spam, or unanswerable:
{{
  "is_valid": false,
  "refusal_reason": "..."
}}

RULES:
- Pick the MOST relevant domain from the list above
- Subdomain is optional (can be null or omitted)
- Confidence should reflect certainty (0.0 to 1.0)
- For questions about power/influence → Strategy
- For questions about thinking/mind/behavior → Psychology
- For questions about systems/complexity → Technology or Economics
- For questions about meaning/ethics/life → Philosophy
- If multiple domains fit, pick the primary one
- If question is off-topic, refuse with clear reason"""

            result = provider.call(
                system_prompt=system_prompt,
                user_prompt=question,
                agent_name="IntentClassifier",
                temperature=0.3,
                max_tokens=150,
                response_format="json"
            )
            
            # Validate and construct response
            is_valid = result.get("is_valid", True)
            
            if not is_valid:
                return IntentResult(
                    domain="Philosophy",  # Dummy value
                    subdomain=None,
                    confidence=0.0,
                    is_valid=False,
                    refusal_reason=result.get("refusal_reason", "Unable to classify query")
                )
            
            domain = result.get("domain", "Philosophy")
            subdomain = result.get("subdomain")
            confidence = float(result.get("confidence", 0.5))
            
            # Validate domain against whitelist
            if not validate_domain(domain):
                # LLM hallucinated a domain - fall back to Philosophy
                domain = "Philosophy"
                confidence = max(0.3, confidence * 0.7)  # Penalize confidence
            
            # Clamp confidence to [0, 1]
            confidence = max(0.0, min(1.0, confidence))
            
            return IntentResult(
                domain=domain,
                subdomain=subdomain,
                confidence=confidence,
                is_valid=True
            )
            
        except ValueError as e:
            # JSON parsing error - LLM returned malformed response
            return IntentResult(
                domain="Philosophy",
                subdomain=None,
                confidence=0.3,
                is_valid=True
            )
        except Exception as e:
            # Any other error (API timeout, etc.) - fail closed
            return IntentResult(
                domain="Philosophy",
                subdomain=None,
                confidence=0.3,
                is_valid=True
            )
