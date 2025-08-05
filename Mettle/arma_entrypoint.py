
from .components.Brehn.chat_bot import ConversationManager
from .components.relationships.friends import FriendshipEngine


ARMA_EXT_INSTANCE=None

class ArmaEntrypoint:
    def __init__(self) -> None:
        self.socialEngine=FriendshipEngine()
        self.conversationManager=ConversationManager()
    
    @staticmethod
    def inst():
        global ARMA_EXT_INSTANCE
        ARMA_EXT_INSTANCE=None
        
        ARMA_EXT_INSTANCE=ArmaEntrypoint()
        return True
    
    @staticmethod
    def deInst():
        global ARMA_EXT_INSTANCE
        ARMA_EXT_INSTANCE=None
        
    def pullSocialEngineArg(self,argName):
        pass