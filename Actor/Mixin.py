class CooperativeUpdateMixin:
    def handle_cooperative_update(self, status_id):
        raise NotImplementedError("Subclasses must implement this method.")