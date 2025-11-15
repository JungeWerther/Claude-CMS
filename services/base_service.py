"""
Base service with support for both direct database access and HTTP client mode.
"""

import os
from typing import Optional

SERVICE_URL = os.getenv("SERVICE_URL")


def is_remote_mode() -> bool:
    """Check if services should use HTTP client mode."""
    return SERVICE_URL is not None


def get_service_url() -> Optional[str]:
    """Get the base service URL if in remote mode."""
    return SERVICE_URL
