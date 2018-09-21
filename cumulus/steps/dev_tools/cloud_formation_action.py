import awacs

import cumulus.policies
import cumulus.policies.cloudformation
import cumulus.types.codebuild.buildaction

from troposphere import iam, codepipeline, GetAtt
from cumulus.chain import step
from cumulus.steps.dev_tools import META_PIPELINE_BUCKET_POLICY_REF


class CloudFormationAction(step.Step):

    def __init__(self,
                 action_name,
                 input_artifact_names,
                 input_template_path,
                 input_template_configuration,
                 stage_name_to_add,
                 stack_name,
                 action_mode):
        """
        :type action_name: basestring Displayed on the console
        :type input_artifact_names: [basestring] List of input artifacts
        :type input_template_path: basestring Full path to cloudformation template (ex. ArtifactName::templatefolder/template.json)
        :type input_configuration: basestring Full path to cloudformation config file (ex. ArtifactName::envfolder/parameters.json)
        :type stage_name_to_add: basestring Name of the pipeline stage to add this action to
        :type stack_name: basestring name of the stack that this action will build
        :type action_mode: cumulus.types.cloudformation.action_mode.ActionMode The actual CloudFormation action to execute
        """
        step.Step.__init__(self)
        self.action_name = action_name
        self.input_artifact_names = input_artifact_names
        self.input_template_path = input_template_path
        self.input_template_configuration = input_template_configuration
        self.stage_name_to_add = stage_name_to_add
        self.stack_name = stack_name
        self.action_mode = action_mode

    def handle(self, chain_context):

        print("Adding action %sstage" % self.action_name)

        policy_name = "CloudFormationPolicy%stage" % chain_context.instance_name
        role_name = "CloudFormationRole%stage" % self.action_name

        cloud_formation_role = iam.Role(
            role_name,
            Path="/",
            AssumeRolePolicyDocument=awacs.aws.Policy(
                Statement=[
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[awacs.sts.AssumeRole],
                        Principal=awacs.aws.Principal(
                            'Service',
                            ["cloudformation.amazonaws.com"]
                        )
                    )]
            ),
            Policies=[
                cumulus.policies.cloudformation.get_policy_cloudformation_general_access(policy_name)
            ],
            ManagedPolicyArns=[
                chain_context.metadata[META_PIPELINE_BUCKET_POLICY_REF]
            ]
        )

        input_artifacts = []
        for artifact_name in self.input_artifact_names:
            input_artifacts.append(codepipeline.InputArtifacts(
                Name=artifact_name
            ))

        cloud_formation_action = cumulus.types.codebuild.buildaction.CloudFormationAction(
            Name=self.action_name,
            InputArtifacts=input_artifacts,
            Configuration={
                'ActionMode': self.action_mode.value,
                'RoleArn': GetAtt(cloud_formation_role, 'Arn'),
                'StackName': self.stack_name,
                'Capabilities': 'CAPABILITY_NAMED_IAM',
                'TemplateConfiguration': self.input_template_configuration,
                'TemplatePath': self.input_template_path
            },
            RunOrder="1"
        )

        chain_context.template.add_resource(cloud_formation_role)

        stage = cumulus.util.template_query.TemplateQuery.get_pipeline_stage_by_name(
            template=chain_context.template,
            stage_name=self.stage_name_to_add
        )

        # TODO accept a parallel action to the previous action, and don't +1 here.
        next_run_order = len(stage.Actions) + 1
        cloud_formation_action.RunOrder = next_run_order
        stage.Actions.append(cloud_formation_action)
