"""
Alexandria Library - Canon Service
Read-only access to books, chapters, and text.
Canon is SACRED. No mutations except by admin ingestion.

INVARIANTS:
- book_text.content is the single source of truth
- Chapters reference offsets, they don't store text
- file_path is internal only, never exposed to users
"""

from typing import Optional, List
from ..db.database import get_db


class CanonService:
    """
    Service for accessing canonical texts.
    Users read through this. It's read-only.
    """
    
    def get_books(
        self,
        domain: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100
    ) -> List[dict]:
        """
        Get all public books, optionally filtered.
        
        Args:
            domain: Filter by domain (Philosophy, Strategy, etc.)
            search: Search in title/author
            limit: Max results
            
        Returns:
            List of book dicts (no file_path - that's internal)
        """
        db = get_db()
        
        query = """
            SELECT id, title, author, domain, subdomain, is_public, created_at
            FROM books
            WHERE is_public = 1
        """
        params = []
        
        if domain:
            query += " AND domain = ?"
            params.append(domain)
        
        if search:
            query += " AND (title LIKE ? OR author LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        query += " ORDER BY title LIMIT ?"
        params.append(limit)
        
        rows = db.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    
    def get_book(self, book_id: str) -> Optional[dict]:
        """Get a single book by ID."""
        db = get_db()
        
        row = db.execute(
            """
            SELECT id, title, author, domain, subdomain, is_public, created_at
            FROM books
            WHERE id = ? AND is_public = 1
            """,
            (book_id,)
        ).fetchone()
        
        return dict(row) if row else None
    
    def get_domains(self) -> List[str]:
        """Get list of unique domains for filtering."""
        db = get_db()
        
        rows = db.execute(
            """
            SELECT DISTINCT domain
            FROM books
            WHERE domain IS NOT NULL AND is_public = 1
            ORDER BY domain
            """
        ).fetchall()
        
        return [row["domain"] for row in rows]
    
    def get_book_count(self) -> int:
        """Get total count of public books."""
        db = get_db()
        
        row = db.execute(
            "SELECT COUNT(*) as count FROM books WHERE is_public = 1"
        ).fetchone()
        
        return row["count"] if row else 0
    
    def get_chapters(self, book_id: str) -> List[dict]:
        """Get all chapters for a book."""
        db = get_db()
        
        rows = db.execute(
            """
            SELECT id, book_id, number, title, start_offset, end_offset
            FROM chapters
            WHERE book_id = ?
            ORDER BY number
            """,
            (book_id,)
        ).fetchall()
        
        return [dict(row) for row in rows]
    
    def get_chapter(self, chapter_id: str) -> Optional[dict]:
        """Get a single chapter by ID."""
        db = get_db()
        
        row = db.execute(
            """
            SELECT id, book_id, number, title, start_offset, end_offset
            FROM chapters
            WHERE id = ?
            """,
            (chapter_id,)
        ).fetchone()
        
        return dict(row) if row else None
    
    def get_chapter_by_number(self, book_id: str, number: int) -> Optional[dict]:
        """Get chapter by book ID and chapter number."""
        db = get_db()
        
        row = db.execute(
            """
            SELECT id, book_id, number, title, start_offset, end_offset
            FROM chapters
            WHERE book_id = ? AND number = ?
            """,
            (book_id, number)
        ).fetchone()
        
        return dict(row) if row else None
    
    def get_chapter_text(self, book_id: str, chapter_id: str) -> str:
        """
        Get the text for a specific chapter.
        
        This extracts text from book_text.content using chapter offsets.
        The chapter table stores offsets, not text - this is by design.
        """
        db = get_db()
        
        # Get the full book text and chapter offsets
        row = db.execute(
            """
            SELECT bt.content, c.start_offset, c.end_offset
            FROM book_text bt
            JOIN chapters c ON c.book_id = bt.book_id
            WHERE bt.book_id = ? AND c.id = ?
            """,
            (book_id, chapter_id)
        ).fetchone()
        
        if not row:
            return ""
        
        content = row["content"]
        start = row["start_offset"]
        end = row["end_offset"]
        
        return content[start:end]
    
    def get_full_text(self, book_id: str) -> str:
        """
        Get the full text of a book.
        Admin use only - prefer get_chapter_text for reading.
        """
        db = get_db()
        
        row = db.execute(
            "SELECT content FROM book_text WHERE book_id = ?",
            (book_id,)
        ).fetchone()
        
        return row["content"] if row else ""
    
    def get_books_by_domain(self, domain: str) -> List[dict]:
        """Get all books in a specific domain."""
        return self.get_books(domain=domain)
    
    def search_books(self, query: str) -> List[dict]:
        """Search books by title or author."""
        return self.get_books(search=query)

