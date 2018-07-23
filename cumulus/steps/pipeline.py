from ..chain import Handler
from ..tropo_helpers.helpers import ResourceQueries as queries

from troposphere import Template, codepipeline, Ref


class Pipeline(Handler):

    def handle(self, template):
        """

        :type template: Template
        """
        super(Pipeline, self).handle()

        generic_pipeline = codepipeline.Pipeline(
            "AppPipeline",
            RoleArn=Ref('TODO-CodePipelineServiceRole'),
            Stages = None,
            ArtifactStore = codepipeline.ArtifactStore(
                Type="S3",
                Location=Ref('TODO-ArtifactStoreS3Location')
            )
        )

        template.add_resource(generic_pipeline)



class Stage(Handler):

    def handle(self, template):
        """

        :type template: troposphere.Template
        """
        super(Stage, self).handle()

        print("Stages found: ")

        queries.get_resource_by_title('AppPipeline')
        # for stage in template.resources

