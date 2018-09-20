
class TemplateRequirements:

    def __init__(self):
        self._required_params = []

    @property
    def params(self):
        return self._required_params

    def add(self, param):
        self._required_params.append(param)
