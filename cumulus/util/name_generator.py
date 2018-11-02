
class NameGenerator:

    def __init__(self, name_generator_template=None):
        self.name_generator_template = name_generator_template

    def create_name(self, name_type, name_text):
        return self.name_generator_template.format(name_type, name_text)
