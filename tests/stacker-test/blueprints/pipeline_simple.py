from stacker.blueprints.base import Blueprint

from cumulus.steps import pipeline


class PipelineSimple(Blueprint):
    """Touch creates a wait condition handle and nothing else.

    For learning / functional testing.
    """

    def create_template(self):

        t = self.template

        deploy_pipeline = pipeline.Pipeline(template=t)
        stage1 = pipeline.Stage(deploy_pipeline)
        stage2 = pipeline.Stage(successor=stage1)
        stage2.handle()

        print("\n\nJust generated this template:")
        print(self.template.__dict__)
        raise ValueError("Don't want to complete yet")
