
import awacs
import troposphere

import awacs.iam
import awacs.aws
import awacs.sts
import awacs.s3
import awacs.logs
import awacs.ec2
import awacs.iam
import awacs.codecommit
import awacs.awslambda

from cumulus.chain import step
import cumulus.steps.dev_tools

from troposphere import codepipeline, Ref, iam
from troposphere.s3 import Bucket, VersioningConfiguration


class Pipeline(step.Step):
    def __init__(self,
                 name,
                 bucket_name,
                 pipeline_policies=None,
                 bucket_policy_statements=None,
                 bucket_kms_key_arn=None,
                 ):
        """

        :type bucket_policy_statements: [awacs.aws.Statement]
        :type bucket: troposphere.s3.Bucket
        :type pipeline_policies: [troposphere.iam.Policy]
        :type bucket_name: the name of the bucket that will be created suffixed with the chaincontext instance name
        """
        step.Step.__init__(self)
        self.name = name
        self.bucket_name = bucket_name
        self.bucket_policy_statements = bucket_policy_statements
        self.pipeline_policies = pipeline_policies or []
        self.bucket_kms_key_arn = bucket_kms_key_arn

    def handle(self, chain_context):
        """
        This step adds in the shell of a pipeline.
         * s3 bucket
         * policies for the bucket and pipeline
         * your next step in the chain MUST be a source stage
        :param chain_context:
        :return:
        """
        # TODO: let (force?) bucket to be injected.
        pipeline_bucket = Bucket(
            "PipelineBucket%s" % self.name,
            BucketName=self.bucket_name,
            VersioningConfiguration=VersioningConfiguration(
                Status="Enabled"
            )
        )

        default_bucket_policies = self.get_default_bucket_policy_statements(pipeline_bucket)

        if self.bucket_policy_statements:
            bucket_access_policy = self.get_bucket_policy(
                pipeline_bucket=pipeline_bucket,
                bucket_policy_statements=self.bucket_policy_statements,
            )
            chain_context.template.add_resource(bucket_access_policy)

        pipeline_bucket_access_policy = iam.ManagedPolicy(
            "PipelineBucketAccessPolicy",
            Path='/managed/',
            PolicyDocument=awacs.aws.PolicyDocument(
                Version="2012-10-17",
                Id="bucket-access-policy%s" % chain_context.instance_name,
                Statement=default_bucket_policies
            )
        )

        chain_context.template.add_resource(pipeline_bucket_access_policy)
        # pipeline_bucket could be a string or Join object.. unit test this.
        chain_context.metadata[cumulus.steps.dev_tools.META_PIPELINE_BUCKET_REF] = Ref(pipeline_bucket)
        chain_context.metadata[cumulus.steps.dev_tools.META_PIPELINE_BUCKET_POLICY_REF] = Ref(
            pipeline_bucket_access_policy)

        # TODO: this can be cleaned up by using a policytype and passing in the pipeline role it should add itself to.
        pipeline_policy = iam.Policy(
            PolicyName="%sPolicy" % self.name,
            PolicyDocument=awacs.aws.PolicyDocument(
                Version="2012-10-17",
                Id="PipelinePolicy",
                Statement=[
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        # TODO: actions here could be limited more
                        Action=[awacs.aws.Action("s3", "*")],
                        Resource=[
                            troposphere.Join('', [
                                awacs.s3.ARN(),
                                Ref(pipeline_bucket),
                                "/*"
                            ]),
                            troposphere.Join('', [
                                awacs.s3.ARN(),
                                Ref(pipeline_bucket),
                            ]),
                        ],
                    ),
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[awacs.aws.Action("kms", "*")],
                        Resource=['*'],
                    ),
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.aws.Action("cloudformation", "*"),
                            awacs.aws.Action("codebuild", "*"),
                        ],
                        # TODO: restrict more accurately
                        Resource=["*"]
                    ),
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.codecommit.GetBranch,
                            awacs.codecommit.GetCommit,
                            awacs.codecommit.UploadArchive,
                            awacs.codecommit.GetUploadArchiveStatus,
                            awacs.codecommit.CancelUploadArchive
                        ],
                        Resource=["*"]
                    ),
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.iam.PassRole
                        ],
                        Resource=["*"]
                    ),
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[
                            awacs.aws.Action("lambda", "*")
                        ],
                        Resource=["*"]
                    )
                ],
            )
        )

        pipeline_service_role = iam.Role(
            "PipelineServiceRole",
            Path="/",
            AssumeRolePolicyDocument=awacs.aws.Policy(
                Statement=[
                    awacs.aws.Statement(
                        Effect=awacs.aws.Allow,
                        Action=[awacs.sts.AssumeRole],
                        Principal=awacs.aws.Principal(
                            'Service',
                            "codepipeline.amazonaws.com"
                        )
                    )]
            ),
            Policies=[pipeline_policy] + self.pipeline_policies
        )

        generic_pipeline = codepipeline.Pipeline(
            "Pipeline",
            RoleArn=troposphere.GetAtt(pipeline_service_role, "Arn"),
            Stages=[],
            ArtifactStore=codepipeline.ArtifactStore(
                Type="S3",
                Location=Ref(pipeline_bucket),
            )
            # TODO: optionally add kms key here
        )

        if self.bucket_kms_key_arn:
            encryption_config = codepipeline.EncryptionKey(
                "ArtifactBucketKmsKey",
                Id=self.bucket_kms_key_arn,
                Type='KMS',
            )
            generic_pipeline.ArtifactStore.EncryptionKey = encryption_config

        pipeline_output = troposphere.Output(
            "PipelineName",
            Description="Code Pipeline",
            Value=Ref(generic_pipeline),
        )

        chain_context.template.add_resource(pipeline_bucket)
        chain_context.template.add_resource(pipeline_service_role)
        chain_context.template.add_resource(generic_pipeline)
        chain_context.template.add_output(pipeline_output)

    def get_default_bucket_policy_statements(self, pipeline_bucket):
        bucket_policy_statements = [
            awacs.aws.Statement(
                Effect=awacs.aws.Allow,
                Action=[
                    awacs.s3.ListBucket,
                    awacs.s3.GetBucketVersioning,
                ],
                Resource=[
                    troposphere.Join('', [
                        awacs.s3.ARN(),
                        Ref(pipeline_bucket),
                    ]),
                ],
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
                    awacs.s3.GetObject,
                    awacs.s3.GetObjectVersion,
                    awacs.s3.PutObject,
                    awacs.s3.ListObjects,
                    awacs.s3.ListBucketMultipartUploads,
                    awacs.s3.AbortMultipartUpload,
                    awacs.s3.ListMultipartUploadParts,
                    awacs.aws.Action("s3", "Get*"),
                ],
                Resource=[
                    troposphere.Join('', [
                        awacs.s3.ARN(),
                        Ref(pipeline_bucket),
                        '/*'
                    ]),
                ],
            )
        ]

        return bucket_policy_statements

    def get_bucket_policy(self, pipeline_bucket, bucket_policy_statements):
        policy = troposphere.s3.BucketPolicy(
            "PipelineBucketPolicy",
            Bucket=troposphere.Ref(pipeline_bucket),
            PolicyDocument=awacs.aws.Policy(
                Statement=bucket_policy_statements,
            ),
        )
        return policy
