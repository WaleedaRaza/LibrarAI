"""
Alexandria Library - Text Companion Agent

PURPOSE: Clarify ONLY the selected text span
FORBIDDEN: general advice, modern extrapolation, cross-book synthesis

This is the most constrained agent.
It can only explain what the user has selected.
It cannot give advice.
It cannot make modern applications.
It cannot reference other texts.

If the question is out of scope, it REFUSES.
"""

from ..config import settings
from .contracts import CompanionResponse


class TextCompanion:
    """
    Section-bound text explanations.
    
    The most constrained agent.
    Stateless. Pure. Replaceable.
    """
    
    def explain(
        self,
        book_title: str,
        chapter_title: str,
        selected_text: str,
        question: str
    ) -> CompanionResponse:
        """
        Explain the selected text in response to a question.
        
        CONSTRAINTS:
        - Only clarifies the selected text
        - No general advice
        - No modern extrapolation
        - No cross-book synthesis
        - Refuses if out of scope
        
        Args:
            book_title: Title of the book
            chapter_title: Title of the chapter
            selected_text: The text the user selected
            question: User's question about the text
            
        Returns:
            CompanionResponse with explanation or refusal
        """
        if settings.USE_MOCK_AGENTS:
            return self._mock_explain(book_title, chapter_title, selected_text, question)
        return self._llm_explain(book_title, chapter_title, selected_text, question)
    
    def _mock_explain(
        self,
        book_title: str,
        chapter_title: str,
        selected_text: str,
        question: str
    ) -> CompanionResponse:
        """
        Mock companion for development.
        Returns a generic but valid response.
        """
        # Simple out-of-scope detection
        question_lower = question.lower()
        
        out_of_scope_signals = [
            "how should i",
            "what should i do",
            "in my life",
            "my situation",
            "advice",
            "today",
            "modern",
            "apply this",
            "other books",
            "what else",
        ]
        
        if any(signal in question_lower for signal in out_of_scope_signals):
            return CompanionResponse(
                explanation="",
                is_valid=False,
                refusal_reason="I can only clarify the text itself, not provide personal advice or modern applications. What specifically about this passage is unclear?",
                suggested_chapter=None
            )
        
        # Generic clarification response
        return CompanionResponse(
            explanation=f"In this passage from '{book_title}', {chapter_title}, the author addresses the concept you've highlighted. The key point is the relationship between the ideas presented and the broader argument being made. Consider the context in which this was written and the audience the author was addressing.",
            is_valid=True,
            refusal_reason=None,
            suggested_chapter=None
        )
    
    def _llm_explain(
        self,
        book_title: str,
        chapter_title: str,
        selected_text: str,
        question: str
    ) -> CompanionResponse:
        """
        Real LLM explanation.
        Requires OPENAI_API_KEY.
        """
        try:
            from openai import OpenAI
            import json
            
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are a text companion. Your ONLY job is to clarify the selected text.

Book: {book_title}
Chapter: {chapter_title}

Selected text:
\"\"\"{selected_text}\"\"\"

STRICT RULES:
1. ONLY clarify the text above. Nothing else.
2. NO personal advice. NO "you should..."
3. NO modern applications. NO "in today's world..."
4. NO references to other books or authors
5. NO synthesis or meta-commentary
6. If the question is out of scope, REFUSE

Respond with ONLY a JSON object:
{{
  "explanation": "Your clarification of the text",
  "is_valid": true
}}

OR if refusing:
{{
  "is_valid": false,
  "refusal_reason": "Why you cannot answer this"
}}
"""
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return CompanionResponse(
                explanation=result.get("explanation", ""),
                is_valid=result.get("is_valid", True),
                refusal_reason=result.get("refusal_reason"),
                suggested_chapter=result.get("suggested_chapter")
            )
            
        except Exception as e:
            # Fail closed: return refusal
            return CompanionResponse(
                explanation="",
                is_valid=False,
                refusal_reason="I couldn't process your question. Please try again.",
                suggested_chapter=None
            )

