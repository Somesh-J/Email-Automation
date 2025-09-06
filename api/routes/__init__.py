"""
Routes package initialization
"""

from . import email_processing, domain_management, monitoring, health, bulk_email, analytics, settings

__all__ = [
    "email_processing",
    "domain_management", 
    "monitoring",
    "health",
    "bulk_email",
    "analytics", 
    "settings"
]
