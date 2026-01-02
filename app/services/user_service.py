"""
Alexandria Library - User Service
Manages user data: saved books, highlights, annotations.
This is mutable data, unlike canon.
"""

from typing import Optional, List
import uuid
from ..db.database import get_db


class UserService:
    """
    Service for user-specific data.
    This is where highlights, saved books, and annotations live.
    """
    
    # -------------------------------------------------------------------------
    # Saved Books
    # -------------------------------------------------------------------------
    
    def get_saved_books(self, user_id: str) -> List[dict]:
        """Get all books saved by a user."""
        db = get_db()
        
        rows = db.execute(
            """
            SELECT b.id, b.title, b.author, b.domain, sb.created_at as saved_at
            FROM saved_books sb
            JOIN books b ON sb.book_id = b.id
            WHERE sb.user_id = ?
            ORDER BY sb.created_at DESC
            """,
            (user_id,)
        ).fetchall()
        
        return [dict(row) for row in rows]
    
    def is_book_saved(self, user_id: str, book_id: str) -> bool:
        """Check if a user has saved a book."""
        db = get_db()
        
        row = db.execute(
            "SELECT 1 FROM saved_books WHERE user_id = ? AND book_id = ?",
            (user_id, book_id)
        ).fetchone()
        
        return row is not None
    
    def save_book(self, user_id: str, book_id: str) -> dict:
        """Save a book to user's library."""
        db = get_db()
        
        save_id = f"save_{uuid.uuid4().hex[:12]}"
        
        db.execute(
            """
            INSERT OR IGNORE INTO saved_books (id, user_id, book_id)
            VALUES (?, ?, ?)
            """,
            (save_id, user_id, book_id)
        )
        db.commit()
        
        return {"id": save_id, "user_id": user_id, "book_id": book_id}
    
    def unsave_book(self, user_id: str, book_id: str) -> bool:
        """Remove a book from user's library."""
        db = get_db()
        
        cursor = db.execute(
            "DELETE FROM saved_books WHERE user_id = ? AND book_id = ?",
            (user_id, book_id)
        )
        db.commit()
        
        return cursor.rowcount > 0
    
    # -------------------------------------------------------------------------
    # Highlights
    # -------------------------------------------------------------------------
    
    def get_highlights(self, user_id: str, chapter_id: str) -> List[dict]:
        """Get all highlights for a user in a specific chapter."""
        db = get_db()
        
        rows = db.execute(
            """
            SELECT id, user_id, chapter_id, start_offset, end_offset, color, created_at
            FROM highlights
            WHERE user_id = ? AND chapter_id = ?
            ORDER BY start_offset
            """,
            (user_id, chapter_id)
        ).fetchall()
        
        return [dict(row) for row in rows]
    
    def get_all_highlights(self, user_id: str, book_id: str) -> List[dict]:
        """Get all highlights for a user across all chapters of a book."""
        db = get_db()
        
        rows = db.execute(
            """
            SELECT h.id, h.chapter_id, h.start_offset, h.end_offset, h.color,
                   c.number as chapter_number, c.title as chapter_title
            FROM highlights h
            JOIN chapters c ON h.chapter_id = c.id
            WHERE h.user_id = ? AND c.book_id = ?
            ORDER BY c.number, h.start_offset
            """,
            (user_id, book_id)
        ).fetchall()
        
        return [dict(row) for row in rows]
    
    def create_highlight(
        self,
        user_id: str,
        chapter_id: str,
        start_offset: int,
        end_offset: int,
        color: str = "yellow"
    ) -> dict:
        """Create a new highlight."""
        db = get_db()
        
        highlight_id = f"hl_{uuid.uuid4().hex[:12]}"
        
        db.execute(
            """
            INSERT INTO highlights (id, user_id, chapter_id, start_offset, end_offset, color)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (highlight_id, user_id, chapter_id, start_offset, end_offset, color)
        )
        db.commit()
        
        return {
            "id": highlight_id,
            "user_id": user_id,
            "chapter_id": chapter_id,
            "start_offset": start_offset,
            "end_offset": end_offset,
            "color": color
        }
    
    def delete_highlight(self, highlight_id: str, user_id: str) -> bool:
        """Delete a highlight (only if owned by user)."""
        db = get_db()
        
        cursor = db.execute(
            "DELETE FROM highlights WHERE id = ? AND user_id = ?",
            (highlight_id, user_id)
        )
        db.commit()
        
        return cursor.rowcount > 0
    
    # -------------------------------------------------------------------------
    # Annotations
    # -------------------------------------------------------------------------
    
    def get_annotation(self, highlight_id: str) -> Optional[dict]:
        """Get annotation for a highlight."""
        db = get_db()
        
        row = db.execute(
            """
            SELECT id, highlight_id, text, created_at, updated_at
            FROM annotations
            WHERE highlight_id = ?
            """,
            (highlight_id,)
        ).fetchone()
        
        return dict(row) if row else None
    
    def create_annotation(self, highlight_id: str, text: str) -> dict:
        """Create or update annotation for a highlight."""
        db = get_db()
        
        annotation_id = f"ann_{uuid.uuid4().hex[:12]}"
        
        # Upsert: update if exists, insert if not
        db.execute(
            """
            INSERT INTO annotations (id, highlight_id, text)
            VALUES (?, ?, ?)
            ON CONFLICT(highlight_id) DO UPDATE SET
                text = excluded.text,
                updated_at = CURRENT_TIMESTAMP
            """,
            (annotation_id, highlight_id, text)
        )
        db.commit()
        
        return {"id": annotation_id, "highlight_id": highlight_id, "text": text}
    
    def delete_annotation(self, annotation_id: str) -> bool:
        """Delete an annotation."""
        db = get_db()
        
        cursor = db.execute(
            "DELETE FROM annotations WHERE id = ?",
            (annotation_id,)
        )
        db.commit()
        
        return cursor.rowcount > 0

