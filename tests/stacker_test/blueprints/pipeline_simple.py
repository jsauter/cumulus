from cumulus.chain import chain, chaincontext
from cumulus.steps import pipeline
from stacker.blueprints.base import Blueprint


class PipelineSimple(Blueprint):
    """Touch creates a wait condition handle and nothing else.

    For learning / functional testing.
    """

    def create_template(self):

        t = self.template
        t.add_description("pipeline spike for dtf")

        # TODO: give to builder
        the_chain = chain.Chain()
        the_chain.add(pipeline.Pipeline(name="uptime-dev"))

        # Example usage if you have a VPC
        # vpc_config = pipeline.VpcConfig(
        #     vpc_id='',
        #     subnets=[
        #       'subnet-1',
        #     ]
        # )

        the_chain.add(pipeline.CodeBuildStage())  # This should hopefully be more valuable, context maybe!

        # t.add_resource(source_bucket)

        chain_context = chaincontext.ChainContext(
            template=t,
            instance_name=self.name
        )

        the_chain.run(chain_context)

        # print("\n\nJust generated this template:")
        # print(t.resources)
        # print()
        # print(t.resources['PipelineServiceRole'].__dict__)
        # print(t.to_yaml())
