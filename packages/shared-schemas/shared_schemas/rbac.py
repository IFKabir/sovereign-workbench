from enum import IntEnum
from pydantic import BaseModel, Field

class RBACRole(IntEnum):
    """RBAC role hierarchy for MRPL sovereign workbench.
    
    Ordered by privilege level - higher value = more authority.
    Comparison operators work naturally: role >= RBACRole.SAFETY_OFFICER
    """
    OPERATOR = 10           # Plant floor operator - advisory queries only
    SAFETY_OFFICER = 20     # Safety team - can approve permits, isolation certs
    PROCESS_ENGINEER = 30   # Process engineering - full analysis access
    PLANT_DIRECTOR = 40     # Plant management - unrestricted access, audit review

ROLE_DESCRIPTIONS = {
    RBACRole.OPERATOR: "Plant floor operator - advisory queries only",
    RBACRole.SAFETY_OFFICER: "Safety team - can approve permits, isolation certs",
    RBACRole.PROCESS_ENGINEER: "Process engineering - full analysis access",
    RBACRole.PLANT_DIRECTOR: "Plant management - unrestricted access, audit review"
}

HITL_REQUIRED_ROLES = {
    "permit_to_work": RBACRole.SAFETY_OFFICER,
    "isolation_certificate": RBACRole.SAFETY_OFFICER,
    "exception_generation": RBACRole.PROCESS_ENGINEER,
    "safety_override": RBACRole.PLANT_DIRECTOR
}

def check_permission(user_role: RBACRole, required_role: RBACRole) -> bool:
    """Check if the given user role meets the required role."""
    return user_role >= required_role

def get_role_display_name(role: RBACRole) -> str:
    """Get the human-readable display name for a role."""
    return role.name.replace("_", " ").title()

class RBACUser(BaseModel):
    """Represents an authenticated user within the system."""
    user_id: str = Field(..., description="Unique identifier for the user")
    username: str = Field(..., description="Username of the user")
    role: RBACRole = Field(..., description="The user's assigned RBAC role")
    department: str = Field(..., description="Department the user belongs to")
    plant_unit: str = Field(..., description="The plant unit the user is assigned to")
