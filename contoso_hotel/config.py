import os
import json
from typing import Dict, Union

def get_configuration(name : str) -> str:
    name = str(name).strip().upper()
    secretStoreFile = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'secrets-store', name)
    if os.path.isfile(secretStoreFile):
        #print("Reading from secrets store")
        with open(secretStoreFile, 'r') as file:
            value = file.read().strip()
    else:
        #print("Reading from environment variable")
        value = os.getenv(name, '')
    return str(value)

class LayoutConfiguration:
    api_baseurl = ''
    chatbot_baseurl = ''
    chatbot_key = ''
    chatbot_frontend_use_chatbot_baseurl = False

    def __init__(self):
        self.api_baseurl = get_configuration('API_BASEURL')
        self.chatbot_baseurl = get_configuration('CHATBOT_BASEURL')
        self.chatbot_key = get_configuration('CHATBOT_KEY')
        self.chatbot_frontend_use_chatbot_baseurl = (get_configuration('CHATBOT_FRONTEND_USE_CHATBOT_BASEURL').lower().strip() in ['true', 't', '1', 'yes', 'y'])
    def _sanitizeBaseUrl(value: str) -> str:
        value = str(value)
        if value.endswith('/'):
            return value[:-1]
        return value
    
    def getChatbotApiKey(self) -> str:
        return str(self.chatbot_key)
    def getChatbotBaseurl(self) -> str:
        return  LayoutConfiguration._sanitizeBaseUrl(self.chatbot_baseurl)
    def getApiBaseurl(self) -> str:
        return LayoutConfiguration._sanitizeBaseUrl(self.api_baseurl)
    def isChatbotEnabled(self) -> bool:
        return str(self.chatbot_baseurl) != ''
    def getDict(self) -> Dict[str, Union[str, bool, int]]:
        return {
            'api_baseurl': str(self.api_baseurl),
            'chatbot_baseurl': str(self.chatbot_baseurl),
            'chatbot_key': str(self.chatbot_key),
            'chatbot_enabled': self.isChatbotEnabled(),
            'chatbot_frontend_use_chatbot_baseurl': self.chatbot_frontend_use_chatbot_baseurl
        }
    def items(self):
        return self.getDict().items()
    def __str__(self):
        return str(self.getDict())
    def __iter__(self):
        return iter(self.getDict().items())
    
def get_layout_configuration() -> LayoutConfiguration:
    return LayoutConfiguration()