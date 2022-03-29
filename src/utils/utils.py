def need_member(member):
    def wrapper_method(method):
        def validation(ref, *args, **kwargs):
            if getattr(ref, member) is None:
                raise Exception(f"You can't call method {method.__name__} with {member} None")
            else:
                return method(ref, *args, **kwargs)

        return validation

    return wrapper_method


def get_actor_display_name(actor, truncate=250):
    """Method to get actor display name"""
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name
