from troposphere import Ref

from cumulus.chain import step
from troposphere.iam import InstanceProfile

from cumulus.util.template_query import TemplateQuery


class InstanceProfileRole(step.Step):

    def __init__(self,
                 instance_profile_name,
                 role):
        step.Step.__init__(self)
        self.instance_profile_name = instance_profile_name
        self.role = role

    def handle(self, chain_context):
        template = chain_context.template

        template.add_resource(self.role)

        try:
            instanceProfile = TemplateQuery.get_resource_by_title(template, self.instance_profile_name)
            instanceProfile.properties['Roles'].append(Ref(self.role))
        except ValueError:
            print('Adding new Instance Profile')
            template.add_resource(InstanceProfile(
                self.instance_profile_name,
                Roles=[Ref(self.role)]
            ))
