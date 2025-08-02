from fastapi import Depends

from r3almX_backend.auth_service.auth_utils import get_current_user
from r3almX_backend.auth_service.user_handler_utils import get_db
from r3almX_backend.auth_service.user_models import User
from r3almX_backend.chat_service.main import chat_service
from r3almX_backend.chat_service.models.rooms_model import RoomsModel

"""
this is where the fun stuff for rooms is implemented such as 
- decentralized data storage for backups
- utility for customization
- digest for plugin registration
- banned user spam detection
- nuking detection

"""


def decentralized_data_storage():
    # Implementation for decentralized data storage for backups
    pass


def utility_for_customization():
    # Implementation for utility for customization
    pass


def digest_for_plugin_registration():
    # Implementation for digest for plugin registration
    pass


def banned_user_spam_detection():
    # Implementation for banned user spam detection
    pass


def nuking_detection():
    # Implementation for nuking detection
    pass
