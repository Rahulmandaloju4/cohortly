"""Role-Based Access Control (RBAC) Module.
Supports 5 demo roles:
- PLATFORM_ADMIN: Full system control, generator, exports, all dashboards and settings.
- ACADEMIC_ADMIN: Full analytics, curriculum, cohort, learner, and validation access.
- INSTRUCTOR: Course management, learner progress, assessment reviews, cohort metrics.
- SUPPORT_STAFF: Exception investigator, audit logs, learner troubleshooting.
- LEARNER: Personal progress, enrolled course details, own timeline.

DEMO DISCLAIMER:
Role enforcement is handled via the X-Demo-Role HTTP header for interactive demonstration
and evaluation purposes. It does not replace production cryptographic authentication (JWT/OAuth2).
"""

from typing import List, Callable
from fastapi import Request, HTTPException, Depends


class Roles:
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    ACADEMIC_ADMIN = "ACADEMIC_ADMIN"
    INSTRUCTOR = "INSTRUCTOR"
    SUPPORT_STAFF = "SUPPORT_STAFF"
    LEARNER = "LEARNER"

    ALL_ROLES = [PLATFORM_ADMIN, ACADEMIC_ADMIN, INSTRUCTOR, SUPPORT_STAFF, LEARNER]
    ADMIN_ROLES = [PLATFORM_ADMIN, ACADEMIC_ADMIN]
    STAFF_ROLES = [PLATFORM_ADMIN, ACADEMIC_ADMIN, INSTRUCTOR, SUPPORT_STAFF]


def get_current_role(request: Request) -> str:
    """Retrieves current demo role from request state set by middleware."""
    role = getattr(request.state, "role", "PLATFORM_ADMIN")
    if role not in Roles.ALL_ROLES:
        role = Roles.PLATFORM_ADMIN
    return role


def require_roles(*allowed_roles: str) -> Callable:
    """Dependency that restricts an endpoint to specific demo roles.
    Raises 403 Forbidden with clear diagnostic feedback if role is unauthorized.
    """
    def role_checker(request: Request) -> str:
        current_role = get_current_role(request)
        if current_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Current role '{current_role}' is not authorized to access this endpoint. Allowed roles: {', '.join(allowed_roles)}.",
            )
        return current_role

    return role_checker
