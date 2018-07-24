
class Chain:

    def __init__(self):
        self._steps = []

    @property
    def steps(self):
        return self._steps

    def add(self, step):
        self._steps.append(step)

    def run(self, template):

        for step in self._steps:
            step.handle(template)
