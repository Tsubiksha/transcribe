"""Compatibility import for the canonical YouTube router.

The active application includes app.api.routes.youtube. Keep this module
pointing there so older imports do not use stale route logic.
"""

from app.api.routes.youtube import router

__all__ = ["router"]
