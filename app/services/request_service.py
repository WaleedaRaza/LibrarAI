"""
Alexandria Library - Request Service
Book request lifecycle - the growth loop.
Users request books, admins approve, canon grows.
"""

from typing import Optional, List
import uuid
from ..db.database import get_db


class RequestService:
    """
    Service for book requests.
    This is how the canon grows - deliberately, not automatically.
    """
    
    def get_user_requests(self, user_id: str) -> List[dict]:
        """Get all book requests by a user."""
        db = get_db()
        
        rows = db.execute(
            """
            SELECT id, title, author, reason, status, admin_notes, created_at, resolved_at
            FROM book_requests
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()
        
        return [dict(row) for row in rows]
    
    def get_pending_requests(self) -> List[dict]:
        """Get all pending requests (admin view)."""
        return self.get_requests_by_status("PENDING")
    
    def get_all_requests(self) -> List[dict]:
        """Get all requests (admin view)."""
        db = get_db()
        
        rows = db.execute(
            """
            SELECT br.id, br.title, br.author, br.reason, br.status, br.created_at,
                   br.admin_notes, br.resolved_at,
                   u.email as requester_email, u.display_name as requester_name
            FROM book_requests br
            JOIN users u ON br.user_id = u.id
            ORDER BY br.created_at DESC
            """
        ).fetchall()
        
        return [dict(row) for row in rows]
    
    def get_requests_by_status(self, status: str) -> List[dict]:
        """Get requests filtered by status (admin view)."""
        db = get_db()
        
        rows = db.execute(
            """
            SELECT br.id, br.title, br.author, br.reason, br.status, br.created_at,
                   br.admin_notes, br.resolved_at,
                   u.email as requester_email, u.display_name as requester_name
            FROM book_requests br
            JOIN users u ON br.user_id = u.id
            WHERE br.status = ?
            ORDER BY br.created_at DESC
            """,
            (status,)
        ).fetchall()
        
        return [dict(row) for row in rows]
    
    def get_request(self, request_id: str) -> Optional[dict]:
        """Get a single request by ID."""
        db = get_db()
        
        row = db.execute(
            """
            SELECT id, user_id, title, author, reason, status, admin_notes, 
                   created_at, resolved_at
            FROM book_requests
            WHERE id = ?
            """,
            (request_id,)
        ).fetchone()
        
        return dict(row) if row else None
    
    def create_request(
        self,
        user_id: str,
        title: str,
        author: Optional[str] = None,
        reason: Optional[str] = None
    ) -> dict:
        """Create a new book request."""
        db = get_db()
        
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        
        db.execute(
            """
            INSERT INTO book_requests (id, user_id, title, author, reason, status)
            VALUES (?, ?, ?, ?, ?, 'PENDING')
            """,
            (request_id, user_id, title, author, reason)
        )
        db.commit()
        
        return {
            "id": request_id,
            "user_id": user_id,
            "title": title,
            "author": author,
            "reason": reason,
            "status": "PENDING"
        }
    
    def cancel_request(self, request_id: str, user_id: str) -> bool:
        """
        Cancel a pending request.
        Only the requester can cancel, and only if still pending.
        """
        db = get_db()
        
        # Only cancel if pending and owned by user
        cursor = db.execute(
            """
            DELETE FROM book_requests
            WHERE id = ? AND user_id = ? AND status = 'PENDING'
            """,
            (request_id, user_id)
        )
        db.commit()
        
        return cursor.rowcount > 0
    
    # -------------------------------------------------------------------------
    # Admin actions
    # -------------------------------------------------------------------------
    
    def approve_request(self, request_id: str, admin_notes: Optional[str] = None) -> bool:
        """Approve a book request (admin only)."""
        db = get_db()
        
        cursor = db.execute(
            """
            UPDATE book_requests
            SET status = 'APPROVED',
                admin_notes = ?,
                resolved_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'PENDING'
            """,
            (admin_notes, request_id)
        )
        db.commit()
        
        return cursor.rowcount > 0
    
    def reject_request(self, request_id: str, admin_notes: Optional[str] = None) -> bool:
        """Reject a book request (admin only)."""
        db = get_db()
        
        cursor = db.execute(
            """
            UPDATE book_requests
            SET status = 'REJECTED',
                admin_notes = ?,
                resolved_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'PENDING'
            """,
            (admin_notes, request_id)
        )
        db.commit()
        
        return cursor.rowcount > 0
    
    def mark_added(self, request_id: str, book_id: str = None) -> bool:
        """Mark a request as fulfilled (book added to canon)."""
        db = get_db()
        
        note = f"Added as {book_id}" if book_id else "Added to library"
        
        cursor = db.execute(
            """
            UPDATE book_requests
            SET status = 'ADDED',
                admin_notes = COALESCE(admin_notes || ' | ', '') || ?,
                resolved_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (note, request_id)
        )
        db.commit()
        
        return cursor.rowcount > 0

