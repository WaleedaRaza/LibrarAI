"""
Alexandria Library - Domain Mapper
Maps between human-readable domain names and stable domain IDs.

This allows the IntentClassifier to continue returning human-readable strings
while the taxonomy gate operates on stable IDs.
"""

from typing import Optional, Tuple


# Bidirectional mapping between display names and IDs
DOMAIN_NAME_TO_ID = {
    "Philosophy": "philosophy",
    "Strategy": "strategy",
    "Psychology": "psychology",
    "Technology": "technology",
    "Economics": "economics",
    "Business": "business",
    "History": "history",
    "Literature": "literature",
    "Science": "science",
    "Security": "security",
    "Self-Improvement": "psychology",  # Map to psychology
}

DOMAIN_ID_TO_NAME = {
    "philosophy": "Philosophy",
    "strategy": "Strategy",
    "psychology": "Psychology",
    "technology": "Technology",
    "economics": "Economics",
    "business": "Business",
    "history": "History",
    "literature": "Literature",
    "science": "Science",
    "security": "security",
}

SUBDOMAIN_NAME_TO_ID = {
    # Philosophy
    "Stoicism": "stoicism",
    "Ethics": "ethics",
    "Epistemology": "ethics",
    "Metaphysics": "ethics",
    "Political Philosophy": "power",  # Map to strategy/power
    "Existentialism": "existentialism",
    
    # Strategy
    "Military Strategy": "military",
    "Game Theory": "negotiation",
    "Negotiation": "negotiation",
    "Decision Making": "negotiation",
    
    # Technology
    "Software Engineering": "software",
    "Systems Design": "systems",
    "Security": "security",
    "Databases": "software",
    
    # Psychology
    "Cognitive Science": "cognitive",
    "Behavioral Economics": "behavioral",
    "Social Psychology": "social",
    "Mindfulness": "mindfulness",
    
    # Economics
    "Microeconomics": "micro",
    "Macroeconomics": "macro",
    "Political Economy": "macro",
    
    # Business
    "Management": "management",
    "Leadership": "management",
    "Entrepreneurship": "entrepreneurship",
    "Productivity": "management",
    "Habits": "mindfulness",
}

SUBDOMAIN_ID_TO_NAME = {
    # Philosophy
    "stoicism": "Stoicism",
    "ethics": "Ethics",
    "existentialism": "Existentialism",
    
    # Strategy
    "military": "Military Strategy",
    "power": "Power Dynamics",
    "negotiation": "Negotiation",
    
    # Technology
    "systems": "Systems Thinking",
    "software": "Software Engineering",
    "security": "Security",
    
    # Psychology
    "mindfulness": "Mindfulness",
    "cognitive": "Cognitive Science",
    "social": "Social Psychology",
    "behavioral": "Behavioral Economics",
    
    # Economics
    "micro": "Microeconomics",
    "macro": "Macroeconomics",
    
    # Business
    "management": "Management",
    "entrepreneurship": "Entrepreneurship",
}


def domain_name_to_id(domain_name: str) -> str:
    """
    Convert human-readable domain name to stable ID.
    
    Args:
        domain_name: "Philosophy", "Strategy", etc.
        
    Returns:
        domain_id: "philosophy", "strategy", etc.
    """
    return DOMAIN_NAME_TO_ID.get(domain_name, domain_name.lower())


def domain_id_to_name(domain_id: str) -> str:
    """
    Convert domain ID to human-readable name.
    
    Args:
        domain_id: "philosophy", "strategy", etc.
        
    Returns:
        domain_name: "Philosophy", "Strategy", etc.
    """
    return DOMAIN_ID_TO_NAME.get(domain_id, domain_id.title())


def subdomain_name_to_id(subdomain_name: Optional[str]) -> Optional[str]:
    """
    Convert human-readable subdomain name to stable ID.
    
    Args:
        subdomain_name: "Stoicism", "Military Strategy", etc.
        
    Returns:
        subdomain_id: "stoicism", "military", etc.
    """
    if not subdomain_name:
        return None
    return SUBDOMAIN_NAME_TO_ID.get(subdomain_name, subdomain_name.lower())


def subdomain_id_to_name(subdomain_id: Optional[str]) -> Optional[str]:
    """
    Convert subdomain ID to human-readable name.
    
    Args:
        subdomain_id: "stoicism", "military", etc.
        
    Returns:
        subdomain_name: "Stoicism", "Military Strategy", etc.
    """
    if not subdomain_id:
        return None
    return SUBDOMAIN_ID_TO_NAME.get(subdomain_id, subdomain_id.title())


def map_to_ids(domain_name: str, subdomain_name: Optional[str]) -> Tuple[str, Optional[str]]:
    """
    Convert domain/subdomain names to IDs.
    
    Args:
        domain_name: Human-readable domain
        subdomain_name: Human-readable subdomain (or None)
        
    Returns:
        Tuple of (domain_id, subdomain_id)
    """
    domain_id = domain_name_to_id(domain_name)
    subdomain_id = subdomain_name_to_id(subdomain_name)
    return (domain_id, subdomain_id)


def map_to_names(domain_id: str, subdomain_id: Optional[str]) -> Tuple[str, Optional[str]]:
    """
    Convert domain/subdomain IDs to names.
    
    Args:
        domain_id: Stable domain ID
        subdomain_id: Stable subdomain ID (or None)
        
    Returns:
        Tuple of (domain_name, subdomain_name)
    """
    domain_name = domain_id_to_name(domain_id)
    subdomain_name = subdomain_id_to_name(subdomain_id)
    return (domain_name, subdomain_name)
