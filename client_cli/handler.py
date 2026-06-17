from abc import ABC, abstractmethod
from network import Message


class MessageHandler(ABC):
    @abstractmethod
    def onConnectOK(self, isMain: bool):
        ...

    @abstractmethod
    def onConnectionFail(self, isMain: bool):
        ...

    @abstractmethod
    def onDisconnected(self, isMain: bool):
        ...

    @abstractmethod
    def onMessage(self, msg: Message):
        ...
