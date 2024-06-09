from abc import ABC, abstractmethod


class Middleware(ABC):
    """Base class for Pbot Middleware.
    """

    @abstractmethod
    def handle_messages(self, messages: list[dict]=[]) -> list[dict]:
        """Abstract method to override with your own business logic.

        There is no promise the message history passed in will not be mutated.

        Args:
            messages (list): A list of messages.

        Returns:
            list: A list of messages.
        """
        raise NotImplementedError

        return messages
