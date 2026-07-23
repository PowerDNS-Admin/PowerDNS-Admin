ADMINISTRATOR_ROLE = 'Administrator'
OPERATOR_ROLE = 'Operator'
ROLE_MANAGERS = (ADMINISTRATOR_ROLE, OPERATOR_ROLE)


def user_update_authorization_error(actor, target=None,
                                    requested_role_name=None,
                                    role_change=False):
    """Return an authorization error for a user update, or ``None``.

    Profile self-service remains allowed. Role changes are restricted to
    administrators and operators, may never target the actor's own role, and
    only administrators may modify administrators or grant that role.
    """
    actor_role_name = actor.role.name

    if (target is not None
            and target.role.name == ADMINISTRATOR_ROLE
            and actor_role_name != ADMINISTRATOR_ROLE):
        return (
            'You do not have permission to modify an Administrator user.'
        )

    if not role_change:
        return None

    if target is not None and target.id == actor.id:
        return 'You cannot change your own role.'

    if actor_role_name not in ROLE_MANAGERS:
        return 'You do not have permission to change user roles.'

    if (requested_role_name == ADMINISTRATOR_ROLE
            and actor_role_name != ADMINISTRATOR_ROLE):
        return (
            'You do not have permission to promote a user to Administrator.'
        )

    return None
