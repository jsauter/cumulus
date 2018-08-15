import troposphere.codepipeline


class SourceS3Action(troposphere.codepipeline.Actions):

    def __init__(self, **kwargs):
        super(SourceS3Action, self).__init__(**kwargs)

        self.ActionTypeId = troposphere.codepipeline.ActionTypeId(
                Category="Source",
                Owner="AWS",
                Version="1",
                Provider='S3',
            )
        self.RunOrder = "1"
