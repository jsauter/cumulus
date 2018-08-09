from cumulus.chain import chain, chaincontext
from cumulus.steps import development
from stacker.blueprints.base import Blueprint


class PipelineSimple(Blueprint):
    """
    An example development that doesn't do anything interesting.
    """

    def create_template(self):

        t = self.template
        t.add_description("development spike for dtf")

        # TODO: give to builder
        the_chain = chain.Chain()
        the_chain.add(development.Pipeline(name="uptime-dev"))

        # Example usage if you have a VPC
        # vpc_config = development.VpcConfig(
        #     vpc_id='',
        #     subnets=[
        #       'subnet-1',
        #     ]
        # )

        the_chain.add(development.CodeBuildStage())  # This should hopefully be more valuable, context maybe!

        chain_context = chaincontext.ChainContext(
            template=t,
            instance_name=self.name
        )

        the_chain.run(chain_context)
