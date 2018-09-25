from troposphere import autoscaling, Ref, FindInMap, Base64, ec2
from cumulus.chain import step
import cumulus.components.userdata.linux
from cumulus.steps.ec2 import META_SECURITY_GROUP_REF


class LaunchConfig(step.Step):

    def __init__(self,
                 meta_data,
                 vpc_id=None,
                 user_data=None, ):

        step.Step.__init__(self)

        self.user_data = user_data
        self.meta_data = meta_data

        self.vpc_id = vpc_id

    def handle(self, chain_context):

        lc_name = 'Lc%s' % chain_context.instance_name

        template = chain_context.template

        template.add_resource(ec2.SecurityGroup(
            "ScalingGroupSecurityGroup",
            GroupDescription="ScalingGroupSecurityGroup description",
            **self._get_security_group_parameters()))

        chain_context.metadata[META_SECURITY_GROUP_REF] = Ref("ScalingGroupSecurityGroup")

        if not self.user_data:
            user_data = cumulus.components.userdata.linux.user_data_for_cfn_init(
                launch_config_name=lc_name,
                asg_name="Asg%s" % chain_context.instance_name,
                configsets='default',  # TODO: Fix this
            )
        else:
            user_data = self.user_data

        launch_config = autoscaling.LaunchConfiguration(
            lc_name,
            UserData=Base64(user_data),
            Metadata=self.meta_data,
            IamInstanceProfile=Ref(chain_context.instance_name),
            **self._get_launch_configuration_parameters(chain_context)
        )

        template.add_resource(launch_config)

    def _get_security_group_parameters(self):
        config = {}

        if self.vpc_id:
            config['VpcId'] = self.vpc_id

        return config

    def _get_launch_configuration_parameters(self, chain_context):

        asg_sg_list = [chain_context.metadata[META_SECURITY_GROUP_REF]]

        parameters = {
            'ImageId': FindInMap('AmiMap',
                                 Ref("AWS::Region"),
                                 Ref('ImageName')),
            'InstanceType': Ref("InstanceType"),
            'KeyName': Ref("SshKeyName"),
            'SecurityGroups': asg_sg_list,
        }

        return parameters
