from cumulus.chain import chaincontext # noqa


class Step:
    """
    Define an interface for handling requests.
    """

    def __init__(self):
        pass

    def handle(self, chain_context):
        # type: (chaincontext.ChainContext) -> None
        raise NotImplemented("handle must be implemented")
