"""
Alexandria Library - Agent Service
Orchestrates the three agents. Enforces contracts.
Handles refusals centrally.

THE THREE AGENTS:
1. Intent Classifier - query → domain
2. Reading Router - domain → chapters
3. Text Companion - selected text → clarification

Agents are STATELESS. They don't touch the database.
This service coordinates them.
"""

from typing import List, Optional
from dataclasses import dataclass

from ..agents.contracts import (
    IntentResult,
    RoutingResult,
    CompanionResponse,
    ReadingRecommendation,
    ReadingPath
)
from ..agents.intent_classifier import IntentClassifier
from ..agents.reading_router import ReadingRouter
from ..agents.text_companion import TextCompanion
from .canon_service import CanonService


@dataclass
class QuestionRouting:
    """Full routing result for a user question."""
    question: str
    intent: IntentResult
    paths: List[ReadingPath]                    # Parallel reading paths
    recommendations: List[ReadingRecommendation] # Flattened (backward compat)
    message: str


class AgentService:
    """
    Orchestrates agents. This is the only place agents are called.
    
    Flow:
    1. User asks question
    2. Intent Classifier → domain/subdomain
    3. Reading Router → book + chapter recommendations
    4. Return structured result
    
    For section chat:
    1. User selects text, asks question
    2. Text Companion → constrained explanation
    3. Return response (or refusal if out of scope)
    """
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.reading_router = ReadingRouter()
        self.text_companion = TextCompanion()
        self.canon = CanonService()
    
    def route_question(self, question: str) -> QuestionRouting:
        """
        Process a user question and route to relevant texts.
        
        This is the core flow: Ask → Route → Read
        Returns PARALLEL reading paths (not ranked recommendations).
        """
        # Step 1: Classify intent
        intent = self.intent_classifier.classify(question)
        
        if not intent.is_valid:
            return QuestionRouting(
                question=question,
                intent=intent,
                paths=[],
                recommendations=[],
                message=intent.refusal_reason or "I couldn't understand your question."
            )
        
        # Step 2: Get available books in this domain
        books = self.canon.get_books_by_domain(intent.domain)
        
        if not books:
            return QuestionRouting(
                question=question,
                intent=intent,
                paths=[],
                recommendations=[],
                message=f"No books available in {intent.domain} yet. You can request one."
            )
        
        # Step 3: Get chapters for each book (for precise routing)
        chapters_by_book = {}
        for book in books[:10]:  # Limit to avoid performance issues
            chapters_by_book[book["id"]] = self.canon.get_chapters(book["id"])
        
        # Step 4: Route to specific chapters via parallel paths
        routing = self.reading_router.route(
            question=question,
            domain=intent.domain,
            subdomain=intent.subdomain,
            available_books=books,
            chapters_by_book=chapters_by_book
        )
        
        if not routing.paths:
            return QuestionRouting(
                question=question,
                intent=intent,
                paths=[],
                recommendations=[],
                message="I found the domain but couldn't identify specific reading. Try browsing the library."
            )
        
        return QuestionRouting(
            question=question,
            intent=intent,
            paths=routing.paths,
            recommendations=routing.recommendations,  # Flattened for backward compat
            message=""
        )
    
    def ask_text_companion(
        self,
        book_title: str,
        chapter_title: str,
        selected_text: str,
        question: str
    ) -> CompanionResponse:
        """
        Ask the Text Companion about selected text.
        
        CONSTRAINTS (enforced by agent):
        - Only clarifies the selected text
        - No general advice
        - No modern extrapolation
        - No cross-book synthesis
        - Refuses if out of scope
        """
        return self.text_companion.explain(
            book_title=book_title,
            chapter_title=chapter_title,
            selected_text=selected_text,
            question=question
        )

