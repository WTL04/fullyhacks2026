# backend/user_actions.py

from backend.world_state import world_state

# ---  Evolution Actions ---


def deploy_disease(target: str, value=None) -> dict:
    if target not in world_state["countries"]:
        return {"status": "failed", "message": f"Unknown country: {target}"}

    world_state["countries"][target]["infected"] = 0.01
    return {
        "status": "success",
        "message": f"Virus deployed in {target}. Patient Zero established.",
    }


def virus_jump(target: str, value=None) -> dict:
    return {"status": "failed", "message": "Not implemented"}


def force_mutation(target: str, value=None) -> dict:
    return {"status": "failed", "message": "Not implemented"}


USER_ACTION_MAP = {
    "deploy_disease": deploy_disease,
    "virus_jump": virus_jump,
    "force_mutation": force_mutation,
}


def dispatch_user_action(action_type: str, target: str, value=None) -> dict:
    if action_type not in USER_ACTION_MAP:
        return {"status": "failed", "message": f"Unknown user action: {action_type}"}

    try:
        return USER_ACTION_MAP[action_type](target, value)
    except Exception as e:
        return {
            "status": "failed",
            "message": f"User action {action_type} crashed: {str(e)}",
        }
