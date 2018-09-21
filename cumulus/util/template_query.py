import troposphere  # noqa
from troposphere import codepipeline


class TemplateQuery:

    def __init__(self):
        pass

    @staticmethod
    def get_resource_by_title(template, title):
        if title not in template.resources:
            raise ValueError("Expected to find resource named %s in template but did not." % title)
        return template.resources[title]

    @staticmethod
    def get_resource_by_type(template, type_to_find):
        # type: (troposphere.Template, type) -> []
        result = []
        for key in template.resources:
            item = template.resources[key]
            if item.__class__ is type_to_find:
                result.append(item)

        # TODO: review: how does this affect other behaviours..
        # if len(result) == 0:
        #     raise ValueError("Expected to find resource of type %s in template but did not." % type_to_find)
        return result

    @staticmethod
    def get_pipeline_stage_by_name(template, stage_name):
        """
        Find the stage in pipelines in a template, and return the stage.

        :type stage_name: basestring The name of the stage to find
        :type template: troposphere.Template  The template to search
        :return: troposphere.codepipeline.Stages
        """
        found_pipelines = TemplateQuery.get_resource_by_type(
            template=template,
            type_to_find=codepipeline.Pipeline)

        if not found_pipelines:
            raise ValueError("Expected to find a pipeline in the template, but did not.")

        pipeline = found_pipelines[0]
        # Alternate way to get this
        # pipeline = TemplateQuery.get_resource_by_title(chain_context.template, 'AppPipeline')
        stages = pipeline.Stages  # type: list
        stage = None
        for s in stages:
            if s.Name == stage_name:
                stage = s

        if not stage:
            raise ValueError("Expected to find stage named: %s but didn't." % stage_name)

        return stage
