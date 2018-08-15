import troposphere.codepipeline


class SourceS3Action(troposphere.codepipeline.Actions):
    """
        This class doesn't do much except set the ActionType to reduce code clutter
    """
    def __init__(self, **kwargs):
        super(SourceS3Action, self).__init__(**kwargs)

        self.ActionTypeId = troposphere.codepipeline.ActionTypeId(
                Category="Source",
                Owner="AWS",
                Version="1",
                Provider='S3',
            )
        self.RunOrder = "1"


class CodeBuildAction(troposphere.codepipeline.Actions):
    """
        This class doesn't do much except set the ActionType to reduce code clutter
    """
    def __init__(self, **kwargs):
        super(CodeBuildAction, self).__init__(**kwargs)

        self.ActionTypeId = troposphere.codepipeline.ActionTypeId(
                Category="Build",
                Owner="AWS",
                Version="1",
                Provider="CodeBuild"
            )
        self.RunOrder = "1"
