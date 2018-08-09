import awacs
import troposphere

import awacs.aws
import awacs.logs
import awacs.s3
import awacs.iam
import awacs.ec2
import awacs.sts


from troposphere import iam,\
    codebuild, codepipeline, Ref, ec2

from cumulus.chain import step
import cumulus.policies
from cumulus.steps.development import META_PIPELINE_BUCKET_POLICY_REF, \
    META_PIPELINE_BUCKET_REF
from cumulus.util.tropo import TemplateQuery


class CodeBuildAction(step.Step):

    def __init__(self, action_name, input_artifact_name, vpc_config=None):
        """
        :type vpc_config.Vpc_Config: required if the codebuild step requires access to the VPC
        """
        step.Step.__init__(self)
        self.input_artifact_name = input_artifact_name
        self.action_name = action_name
        self.vpc_config = vpc_config

    def handle(self, chain_context):

        # previous_stage_output = chain_context.metadata[META_LAST_STAGE_OUTPUT]
        print("handling........the.......%s.....stage" % self.action_name)
        codebuild_policy = iam.Policy(
            PolicyName="CodeBuildPolicy%s" % chain_context.instance_name,
            PolicyDocument=awacs.aws.PolicyDocument(
                Version="2012-10-17",
                Id="CodeBuildPolicyForPipeline",
                Statement=[
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.aws.Action("cloudformation", "*"),
                            awacs.aws.Action("ec2", "*"),
                            awacs.aws.Action("route53", "*"),
                            awacs.aws.Action("iam", "*"),
                            awacs.aws.Action("elasticloadbalancing", "*"),
                            awacs.aws.Action("s3", "*"),
                            awacs.aws.Action("autoscaling", "*"),
                            awacs.aws.Action("apigateway", "*"),
                            awacs.aws.Action("cloudwatch", "*"),
                            awacs.aws.Action("cloudfront", "*"),
                            awacs.aws.Action("rds", "*"),
                            awacs.aws.Action("dynamodb", "*"),
                            awacs.aws.Action("lambda", "*"),
                            awacs.aws.Action("sqs", "*"),
                            awacs.aws.Action("events", "*"),
                            awacs.iam.PassRole,
                        ],
                        Resource=["*"]
                    ),
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.logs.CreateLogGroup,
                            awacs.logs.CreateLogStream,
                            awacs.logs.PutLogEvents,
                        ],
                        # TODO: restrict more accurately
                        Resource=["*"]
                    ),
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.s3.HeadBucket,
                        ],
                        Resource=[
                            '*'
                        ]
                    ),
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.aws.Action('ec2', 'Describe*'),
                        ],
                        # TODO: restrict more accurately.  What does codebuild need?
                        Resource=[
                            "*"
                        ]
                    ),
                    cumulus.policies.POLICY_VPC_CONFIG
                ]
            )
        )

        codebuild_role = iam.Role(
            "CodeBuildServiceRole",
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
            Policies=[
                codebuild_policy
            ],
            ManagedPolicyArns=[
                chain_context.metadata[META_PIPELINE_BUCKET_POLICY_REF]
            ]
        )

        # TODO: make injectable
        environment = codebuild.Environment(
            ComputeType='BUILD_GENERAL1_SMALL',
            Image='aws/codebuild/python:2.7.12',
            Type='LINUX_CONTAINER',
            EnvironmentVariables=[
                # TODO: allow these to be injectable.
                {'Name': 'PIPELINE_BUCKET', 'Value': chain_context.metadata[META_PIPELINE_BUCKET_REF]}
            ],
        )

        project = self.create_project(
            chain_context=chain_context,
            codebuild_role=codebuild_role,
            codebuild_environment=environment
        )

        code_build_action = codepipeline.Actions(
            Name=self.action_name,
            InputArtifacts=[
                codepipeline.InputArtifacts(Name=self.input_artifact_name)
            ],
            ActionTypeId=codepipeline.ActionTypeId(
                Category="Build",
                Owner="AWS",
                Version="1",
                Provider="CodeBuild"
            ),
            Configuration={'ProjectName': Ref(project)},
            RunOrder="1"
        )

        # TODO fetch stage, and add the action above to it.
        # code_build_stage = codepipeline.Stages(
        #     Name=self.stage_name,
        #     Actions=[
        #         # These will have to be filled out by a subsequent action step.
        #     ]
        # )

        chain_context.template.add_resource(codebuild_role)
        chain_context.template.add_resource(project)

        found_pipeline = TemplateQuery.get_resource_by_type(
            template=chain_context.template,
            type_to_find=codepipeline.Pipeline)[0]
        stages = found_pipeline.properties['Stages']  # type: list

        print(stages.count(stages))
        stages['Actions'].append(code_build_action)

        raise ValueError("got stages")

    def create_project(self, chain_context, codebuild_role, codebuild_environment):

        artifacts = codebuild.Artifacts(Type='CODEPIPELINE')

        vpc_config = {}

        # Configure vpc if available
        if self.vpc_config:
            sg = ec2.SecurityGroup(
                "CodebBuild%sSG" % chain_context.instance_name,
                GroupDescription="Gives codebuild access to VPC",
                VpcId=self.vpc_config.vpc_id,
                SecurityGroupEgress=[
                    {
                        "IpProtocol": "-1",
                        "CidrIp": "0.0.0.0/0",
                        "FromPort": "0",
                        "ToPort": "65535",
                    }
                ],
            )
            chain_context.template.add_resource(sg)
            vpc_config = {'VpcConfig': codebuild.VpcConfig(
                    VpcId=self.vpc_config.vpc_id,
                    Subnets=self.vpc_config.subnets,
                    SecurityGroupIds=[Ref(sg)],
                )}

        project = codebuild.Project(
            "project%s" % chain_context.instance_name,
            DependsOn=codebuild_role,
            Artifacts=artifacts,
            Environment=codebuild_environment,
            Name="project-%s" % chain_context.instance_name,
            ServiceRole=troposphere.GetAtt(codebuild_role, 'Arn'),
            Source=codebuild.Source(
                "Deploy",
                Type='CODEPIPELINE',
            ),
            **vpc_config
        )

        return project

#
# source_stage = codepipeline.Stages(
#     Name="SourceStage",
#     Actions=[
#         codepipeline.Actions(
#             Name="SourceAction",
#             ActionTypeId=codepipeline.ActionTypeId(
#                 Category="Source",
#                 Owner="AWS",
#                 Version="1",
#                 Provider='S3',
#             ),
#             OutputArtifacts=[
#                 codepipeline.OutputArtifacts(
#                     Name=SOURCE_STAGE_OUTPUT_NAME
#                 )
#             ],
#             Configuration={
#                 "S3Bucket": Ref(pipeline_bucket),
#                 "S3ObjectKey": self.artifact_path
#             },
#             RunOrder="1"
#         )
#     ]
# )
