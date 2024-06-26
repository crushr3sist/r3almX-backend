# It's a class that contains constants.
# Importing the routes from the auth_routes and user_handler files.
from typing import Final


class UsersConfig(object):
    SECRET_KEY: Final = (
        "f25f387daf523bf5013aa6739050537405c2d3c0c78e96957a57fe3012b0f117"
    )
    ALGORITHM: Final = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: Final = 30
    GOOGLE_CLIENT_ID = (
        "1033716509262-h52etdps8cab2p2ab7gfh8li40u8opsa.apps.googleusercontent.com"
    )
    GOOGLE_CLIENT_SECRET = "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"
    GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback"
