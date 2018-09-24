import awacs
import awacs.aws
import awacs.ec2
import awacs.iam
import awacs.logs
import awacs.s3
import awacs.sts
from troposphere import iam

import cumulus.policies
import cumulus.policies.codebuild
import cumulus.types.codebuild.buildaction
import cumulus.util.template_query
from cumulus.chain import step
from cumulus.steps.dev_tools import META_PIPELINE_BUCKET_POLICY_REF


class ApprovalAction(step.Step):

    def __init__(self,
                 action_name,
                 stage_name_to_add):
        """
        :type stage_name_to_add: basestring Stage name to add the action to.
        :type action_name: basestring Displayed on the console
        """
        step.Step.__init__(self)
        self.action_name = action_name
        self.stage_name_to_add = stage_name_to_add

    def handle(self, chain_context):

        print("Adding approval action %s." % self.action_name)

        policy_name = "CodeBuildPolicy%sStage" % chain_context.instance_name
        role_name = "CodeBuildRole%sStage" % self.action_name

        codebuild_role = iam.Role(
            role_name,
            Path="/",
            AssumeRolePolicyDocument=awacs.aws.Policy(
                Statement=[
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[awacs.sts.AssumeRole],
                        Principal=awacs.aws.Principal(
                            'Service',
                            "codebuild.amazonaws.com"
                        )
                    )]
            ),
            Policies=[  # TODO: policy 'could' be reduced to executing cfn approvals
                cumulus.policies.codebuild.get_policy_code_build_general_access(policy_name)
            ],
            ManagedPolicyArns=[
                chain_context.metadata[META_PIPELINE_BUCKET_POLICY_REF]
            ]
        )

        approval_action = cumulus.types.codebuild.buildaction.ApprovalAction(
            Name=self.action_name,
            RunOrder="1"
        )

        chain_context.template.add_resource(codebuild_role)

        template = chain_context.template
        stage_to_add = self.stage_name_to_add

        stage = cumulus.util.template_query.TemplateQuery.get_pipeline_stage_by_name(
            template=template,
            stage_name=stage_to_add,
        )

        next_run_order = len(stage.Actions) + 1
        approval_action.RunOrder = next_run_order
        stage.Actions.append(approval_action)
