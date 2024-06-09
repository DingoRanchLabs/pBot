"""Transceiver-based Models.

This is a temporary implementation. A shim-layer.
"""

class Server():
    """Stand-In for a future model.
    """

    id = None
    name = None
    parse = 1
    respond = 1

    def mapping(self) -> dict[str, any]:
        """Future proofing this class.

        Returns:
            dict[str, any]: A template respresentation.
        """
        return {
            "id": self.id,
            "name": self.name,
            "parse": self.parse,
            "respond": self.respond
        }

class Channel():
    """Stand-In for a future model.
    """

    id = None
    name = None
    server_id = None
    parse = 1
    respond = 0

    def mapping(self) -> dict[str, any]:
        """Future proofing this class.

        Returns:
            dict[str, any]: A template respresentation.
        """
        return {
            "id": self.id,
            "name": self.name,
            "server_id": self.server_id,
            "parse": self.parse,
            "respond": self.respond
        }

class User():
    """Stand-In for a future model.
    """

    id = None
    name = None
    parse = 1
    respond = 1

    def mapping(self) -> dict[str, any]:
        """Future proofing this class.

        Returns:
            dict[str, any]: A template respresentation.
        """
        return {
            "id": self.id,
            "name": self.name,
            "parse": self.parse,
            "respond": self.respond
        }

class Message():
    """Stand-In for a future model.
    """

    JSON_TEMPLATE = {
        "id": None,
        "time": None,
        "content": None,
        "read": None,
        "response": None,
        "origin": {
            "server": {
                "id": None,
                "name": None,
                "channel": {
                    "id": None,
                    "name": None,
                }
            }
        },
        "user": {
            "id": None,
            "bot": 0,
            "name": None,
            "nick": None,
            "avatar": None,
        },
        "objects": {
            "links": [],
            "attachments": []
        }
    }

    def mapping(self) -> dict[str, any]:
        """Future proofing this class.

        Returns:
            dict[str, any]: A template respresentation.
        """
        return self.JSON_TEMPLATE

class Attachment():
    """Stand-In for a future model.
    """

    id = None
    url = None
    filename = None

    def mapping(self) -> dict[str, any]:
        """Future proofing this class.

        Returns:
            dict[str, any]: A template respresentation.
        """
        return {
            "id": self.id,
            "url": self.url,
            "filename": self.filename
        }
