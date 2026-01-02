"""
Alexandria Library - Taxonomy Gate
Maps domains/subdomains to candidate book_ids.

This is the constraint that keeps the router grounded.
It CANNOT recommend books that aren't in the taxonomy.

INVARIANT: All book_ids must exist in the books table.
MAINTENANCE: Update when new books are added to match their domain/subdomain.
"""

from typing import List, Set, Optional
from dataclasses import dataclass


@dataclass
class TaxonomyMapping:
    """Maps a domain (and optional subdomain) to book IDs."""
    domain: str
    subdomain: Optional[str]
    book_ids: List[str]
    version: int = 1  # Increment when taxonomy changes (for cache invalidation)


# =============================================================================
# TAXONOMY VERSION
# Increment this when you change the mappings below (invalidates routing cache)
# =============================================================================
TAXONOMY_VERSION = 1


# =============================================================================
# DOMAIN → BOOK_IDS MAPPINGS
# 
# These are HARDCODED for now. In production, this should come from:
# - books table with domain/subdomain fields
# - OR a separate taxonomy table
# - OR a config file
#
# For V1: Hardcode based on actual books in DB
# =============================================================================

TAXONOMY: List[TaxonomyMapping] = [
    # Philosophy
    TaxonomyMapping(
        domain="Philosophy",
        subdomain="Stoicism",
        book_ids=["book_d9d95145167f"]  # Meditations
    ),
    TaxonomyMapping(
        domain="Philosophy",
        subdomain=None,
        book_ids=["book_d9d95145167f"]  # Meditations (catch-all for Philosophy)
    ),
    
    # Strategy
    TaxonomyMapping(
        domain="Strategy",
        subdomain="Military Strategy",
        book_ids=["book_e500fb226315"]  # The Art of War
    ),
    TaxonomyMapping(
        domain="Strategy",
        subdomain="Political Philosophy",
        book_ids=["book_062ae004ce4a"]  # The 48 Laws of Power
    ),
    TaxonomyMapping(
        domain="Strategy",
        subdomain=None,
        book_ids=[
            "book_e500fb226315",  # The Art of War
            "book_062ae004ce4a"   # The 48 Laws of Power
        ]
    ),
    
    # Technology / Systems
    TaxonomyMapping(
        domain="Technology",
        subdomain="Systems Design",
        book_ids=["book_5e3b6dc26640"]  # Thinking in Systems
    ),
    TaxonomyMapping(
        domain="Technology",
        subdomain=None,
        book_ids=["book_5e3b6dc26640"]
    ),
    
    # Psychology / Self-Improvement
    TaxonomyMapping(
        domain="Psychology",
        subdomain="Mindfulness",
        book_ids=["book_aaf47b37c1b4"]  # Miracle of Mindfulness
    ),
    TaxonomyMapping(
        domain="Psychology",
        subdomain=None,
        book_ids=["book_aaf47b37c1b4"]
    ),
    
    # Business / Economics (map to Strategy for now)
    TaxonomyMapping(
        domain="Business",
        subdomain=None,
        book_ids=["book_062ae004ce4a"]  # The 48 Laws of Power
    ),
    TaxonomyMapping(
        domain="Economics",
        subdomain=None,
        book_ids=["book_5e3b6dc26640"]  # Thinking in Systems
    ),
    
    # Catch-all fallback
    TaxonomyMapping(
        domain="Self-Improvement",
        subdomain=None,
        book_ids=["book_aaf47b37c1b4"]
    ),
]


# Build lookup index for fast access
_TAXONOMY_INDEX: dict = {}


def _build_index():
    """Build domain+subdomain lookup index."""
    global _TAXONOMY_INDEX
    _TAXONOMY_INDEX.clear()
    
    for mapping in TAXONOMY:
        key = f"{mapping.domain}::{mapping.subdomain or '*'}"
        if key not in _TAXONOMY_INDEX:
            _TAXONOMY_INDEX[key] = []
        _TAXONOMY_INDEX[key].extend(mapping.book_ids)


# Build index on module load
_build_index()


# =============================================================================
# PUBLIC API
# =============================================================================

def get_candidate_books(
    domain: str,
    subdomain: Optional[str] = None,
    max_books: int = 12
) -> List[str]:
    """
    Get candidate book IDs for a domain/subdomain.
    
    Lookup strategy:
    1. Try exact match: domain + subdomain
    2. Fallback to domain + wildcard (subdomain=None)
    3. Return empty list if no match
    
    Args:
        domain: Primary domain
        subdomain: Optional subdomain
        max_books: Cap on number of books returned
        
    Returns:
        List of book_ids (max 12)
    """
    candidates: Set[str] = set()
    
    # Try exact match first
    if subdomain:
        exact_key = f"{domain}::{subdomain}"
        if exact_key in _TAXONOMY_INDEX:
            candidates.update(_TAXONOMY_INDEX[exact_key])
    
    # Fallback to domain wildcard
    wildcard_key = f"{domain}::*"
    if wildcard_key in _TAXONOMY_INDEX:
        candidates.update(_TAXONOMY_INDEX[wildcard_key])
    
    # Cap at max_books
    return list(candidates)[:max_books]


def get_taxonomy_version() -> int:
    """Get current taxonomy version (for cache keys)."""
    return TAXONOMY_VERSION


def validate_book_id(book_id: str) -> bool:
    """Check if a book_id exists in ANY taxonomy mapping."""
    return any(book_id in mapping.book_ids for mapping in TAXONOMY)


def get_all_taxonomy_book_ids() -> Set[str]:
    """Get all book IDs referenced in taxonomy."""
    all_ids: Set[str] = set()
    for mapping in TAXONOMY:
        all_ids.update(mapping.book_ids)
    return all_ids


# =============================================================================
# ADMIN/MAINTENANCE HELPERS
# =============================================================================

def get_taxonomy_coverage() -> dict:
    """Get statistics about taxonomy coverage."""
    return {
        "total_mappings": len(TAXONOMY),
        "unique_books": len(get_all_taxonomy_book_ids()),
        "domains": len(set(m.domain for m in TAXONOMY)),
        "version": TAXONOMY_VERSION,
        "mappings_by_domain": {
            domain: len([m for m in TAXONOMY if m.domain == domain])
            for domain in set(m.domain for m in TAXONOMY)
        }
    }


def rebuild_taxonomy_from_db(books: List[dict]):
    """
    Helper to rebuild taxonomy from database books.
    NOT IMPLEMENTED YET - for future use.
    
    Would query books table, group by domain/subdomain,
    and regenerate TAXONOMY list.
    """
    raise NotImplementedError("Dynamic taxonomy rebuild not yet implemented")

