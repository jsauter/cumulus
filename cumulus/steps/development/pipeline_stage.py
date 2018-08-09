from troposphere import codepipeline

from cumulus.chain import step
from cumulus.util.tropo import TemplateQuery


class PipelineStage(step.Step):

    def __init__(self, stage_name, previous_stage_name):
        """
        :type vpc_config.Vpc_Config: required if the codebuild step requires access to the VPC
        """
        step.Step.__init__(self)
        self.previous_stage_name = previous_stage_name
        self.stage_name = stage_name

    def handle(self, chain_context):

        code_build_stage = codepipeline.Stages(
            Name=self.stage_name,
            Actions=[
                # These will have to be filled out by a subsequent action step.
            ]
        )

        found_pipeline = TemplateQuery.get_resource_by_type(
            template=chain_context.template,
            type_to_find=codepipeline.Pipeline)[0]
        stages = found_pipeline.properties['Stages']  # type: list

        stages.append(code_build_stage)

        print("Added stage to pipeline %s" % stages.count(stages))
