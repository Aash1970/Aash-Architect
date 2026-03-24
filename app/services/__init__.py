# Lazy imports to prevent circular dependency issues during testing.
# Import directly from submodules for performance-sensitive paths.

__all__ = [
    "DataService",
    "AuthService", "AuthError",
    "CVService", "CVServiceError",
    "RoleService", "PermissionDeniedError",
    "TierService", "TierGateError",
    "ATSService", "ATSServiceError",
]


def __getattr__(name):
    if name == "DataService":
        from app.services.data_service import DataService
        return DataService
    if name in ("AuthService", "AuthError"):
        import app.services.auth_service as _m
        return getattr(_m, name)
    if name in ("CVService", "CVServiceError"):
        import app.services.cv_service as _m
        return getattr(_m, name)
    if name in ("RoleService", "PermissionDeniedError"):
        import app.services.role_service as _m
        return getattr(_m, name)
    if name == "TierService":
        from app.services.tier_service import TierService
        return TierService
    if name == "TierGateError":
        from app.tier.tier_rules import TierGateError
        return TierGateError
    if name in ("ATSService", "ATSServiceError"):
        import app.services.ats_service as _m
        return getattr(_m, name)
    raise AttributeError(f"module 'app.services' has no attribute {name!r}")
