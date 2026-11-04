"""Role-Based Access Control (RBAC) Module.
Supports 5 demo roles:
- PLATFORM_ADMIN: Full system control, generator, exports, all dashboards and settings.
- ACADEMIC_ADMIN: Full analytics, curriculum, cohort, learner, and validation access.
- INSTRUCTOR: Course management, learner progress, assessment reviews, cohort metrics.
- SUPPORT_STAFF: Exception investigator, audit logs, learner troubleshooting.
- LEARNER: Personal progress, enrolled course details, own timeline.

DEMO DISCLAIMER:
Role and identity context are handled via the client-controlled X-Demo-Role and X-Demo-Learner-Id
HTTP headers strictly for interactive demonstration, local testing, and evaluation purposes.
These headers are client-supplied and are NOT tamper-proof or secure production authentication.
Production deployments MUST replace these headers with server-verified cryptographic tokens
(e.g., signed JWT/OIDC claims issued by an identity provider), deriving the authenticated user's
identity and role boundaries entirely from validated token claims.
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


def get_current_learner_id(request: Request) -> str:
    """Retrieves current demo learner ID from request state or header (defaults to LRN-000001).
    NOTE: In production, learner identity must be extracted from verified JWT claims (e.g. 'sub').
    """
    learner_id = getattr(request.state, "learner_id", None)
    if not learner_id:
        learner_id = request.headers.get("X-Demo-Learner-Id", "LRN-000001")
    return learner_id


def verify_learner_ownership(request: Request, target_learner_id: str) -> None:
    """Enforces that a user in the LEARNER role can only access their own profile/activity.
    Administrative and staff roles (PLATFORM_ADMIN, ACADEMIC_ADMIN, INSTRUCTOR, SUPPORT_STAFF)
    bypass this check and can inspect any learner's records.

    NOTE: This prevents a client who claims identity 'own_id' from accessing 'target_learner_id'.
    In production, 'own_id' must be derived from cryptographically verified server-side session/JWT tokens.
    """
    current_role = get_current_role(request)
    if current_role == Roles.LEARNER:
        own_id = get_current_learner_id(request)
        if own_id != target_learner_id:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Current role 'LEARNER' with ID '{own_id}' is not authorized to access records of learner '{target_learner_id}'. Changing the learner ID in the URL is restricted.",
            )


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
