from slowapi import Limiter
from slowapi.util import get_remote_address

# Define the limiter centrally to avoid circular imports
limiter = Limiter(key_func=get_remote_address, default_limits=["60 per minute"])
