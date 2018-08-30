from troposphere import codepipeline

from cumulus.chain import step
from cumulus.util.tropo import TemplateQuery


class PipelineStage(step.Step):

    def __init__(self, stage_name):
        """
        :type previous_stage_name: basestring Optional: do not set if this is a source stage
        :type vpc_config.Vpc_Config: required if the codebuild step requires access to the VPC
        """
        step.Step.__init__(self)
        self.stage_name = stage_name
        self._actions = []  # type: step.Step[]

    @property
    def actions(self):
        return self._actions

    def add_action(self, action):
        """
        Currently actions are just type Step, however # TODO: only Stage Actions should be allowed
        :param action: step.Step
        :return:
        """
        self._actions.append(action)

    def handle(self, chain_context):

        pipeline_stage = codepipeline.Stages(
            Name=self.stage_name,
            Actions=[
                # These will have to be filled out by a subsequent action step.
            ]
        )

        found_pipeline = TemplateQuery.get_resource_by_type(
            template=chain_context.template,
            type_to_find=codepipeline.Pipeline)[0]
        stages = found_pipeline.properties['Stages']  # type: list

        stages.append(pipeline_stage)

        for action in self._actions:
            action.stage_name_to_add = self.stage_name  # TODO: refactor so this is typed. multiple inheritance?
            action.handle(chain_context=chain_context)

        print("Added stage to pipeline %s" % stages.count(stages))
