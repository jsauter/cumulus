import troposphere  # noqa


class TemplateQuery:

    @staticmethod
    def get_resource_by_title(template, title):
        return template.resources[title]

    @staticmethod
    def get_resource_by_type(template, type_to_find):
        # type: (troposphere.Template, type) -> []
        result = []
        for key in template.resources:
            item = template.resources[key]
            if item.__class__ is type_to_find:
                result.append(item)
        return result
