from cumulus.chain import step
from cumulus.util.template_query import TemplateQuery
from troposphere import autoscaling


class BlockDeviceData(step.Step):

    def __init__(self,
                 volume):
        step.Step.__init__(self)
        self.volume = volume

    def handle(self, chain_context):
        launchConfig = TemplateQuery.get_resource_by_type(template=chain_context.template,
                                                          type_to_find=autoscaling.LaunchConfiguration)[0]
        launchConfig.properties['BlockDeviceMappings'] = [self.volume]
