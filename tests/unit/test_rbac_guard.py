import pytest
from shared_schemas.rbac import RBACRole, check_permission, get_role_display_name, ROLE_DESCRIPTIONS, HITL_REQUIRED_ROLES

def test_rbac_role_hierarchy():
    assert RBACRole.OPERATOR < RBACRole.SAFETY_OFFICER
    assert RBACRole.SAFETY_OFFICER < RBACRole.PROCESS_ENGINEER
    assert RBACRole.PROCESS_ENGINEER < RBACRole.PLANT_DIRECTOR
    
    # Operators cannot issue permits
    assert check_permission(user_role=RBACRole.OPERATOR, required_role=RBACRole.SAFETY_OFFICER) is False
    # Safety Officers can approve permits
    assert check_permission(user_role=RBACRole.SAFETY_OFFICER, required_role=RBACRole.SAFETY_OFFICER) is True
    # Directors have full permission
    assert check_permission(user_role=RBACRole.PLANT_DIRECTOR, required_role=RBACRole.OPERATOR) is True

def test_role_descriptions_and_display():
    assert get_role_display_name(RBACRole.SAFETY_OFFICER) == "Safety Officer"
    assert get_role_display_name(RBACRole.PROCESS_ENGINEER) == "Process Engineer"
    assert len(ROLE_DESCRIPTIONS) == 4
    assert "permit_to_work" in HITL_REQUIRED_ROLES
