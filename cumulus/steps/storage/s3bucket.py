from troposphere.s3 import Bucket, VersioningConfiguration

from cumulus.chain import step


class S3Bucket(step.Step):
    def __init__(self,
                 logical_name,
                 bucket_name,
                 # bucket_policy_statements=None,
                 ):
        """

        :type bucket_name: the name of the bucket that will be created suffixed with the chaincontext instance name
        :type bucket_policy_statements: [awacs.aws.Statement]
        """
        step.Step.__init__(self)
        self.logical_name = logical_name
        self.bucket_name = bucket_name
        # TODO: this property is a vistigial one from when this was ripped out of the pipeline,
        # however, leaving it here as it is surely useful if you want to just create a bucket
        # with some policies.
        # self.bucket_policy_statements = bucket_policy_statements

    def handle(self, chain_context):
        """
        This step adds in the shell of a pipeline.
         * s3 bucket
         * policies for the bucket and pipeline
         * your next step in the chain MUST be a source stage
        :param chain_context:
        :return:
        """

        bucket = Bucket(
            self.logical_name,
            BucketName=self.bucket_name,
            VersioningConfiguration=VersioningConfiguration(
                Status="Enabled"
            )
        )

        chain_context.template.add_resource(bucket)

        print("Added bucket: " + self.logical_name)
