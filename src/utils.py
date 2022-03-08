def need_member(member):
    def wrapper_method(method):
        def validation(ref, *args, **kwargs):
            if getattr(ref, member) is None:
                raise Exception(f"You can't call method {method.__name__} with {member} None")
            else:
                return method(ref, *args, **kwargs)

        return validation

    return wrapper_method
