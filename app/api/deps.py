"""FastAPI dependencies — authentication and shared injections.

Currently implements a simple Bearer token check against API_SECRET_KEY.
To upgrade to JWT validation, replace the body of `require_api_key` with
a proper JWT decode + claims check (e.g. using python-jose or PyJWT).
"""

import logging
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.exceptions import UnauthorizedError

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)


async def require_api_key(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_scheme),
    ],
) -> str:
    """
    Validate the Authorization: Bearer <token> header.

    Returns the raw token string if valid.
    Raises UnauthorizedError (HTTP 401) if missing or wrong.

    Upgrade path:
        Replace the equality check with a JWT.decode() call and
        extract caller_id from the token claims for audit logging.
    """
    if credentials is None:
        raise UnauthorizedError("Authorization header is required")

    if credentials.credentials != settings.API_SECRET_KEY:
        logger.warning("Invalid API key attempt")
        raise UnauthorizedError("Invalid API key")

    return credentials.credentials


# Re-export the type alias for cleaner endpoint signatures
ApiKey = Annotated[str, Depends(require_api_key)]
