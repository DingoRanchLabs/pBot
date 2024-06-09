class Response():
    """Stand-In for a future model.

    Attributes:
        TEMPLATE (dict): The source of truth for what a Response will be.
    """

    TEMPLATE = {
        "user": None,
        "content": None,
        "message": None,
        "channel": None,
        "server": None,
        "sent": "",
        "time": None
    }

    def mapping(self) -> dict[str, any]:
        """Future proofing this class.

        Returns:
            dict[str, any]: A template respresentation.
        """

        return self.TEMPLATE
