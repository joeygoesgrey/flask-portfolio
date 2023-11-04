import os
from decouple import config


class Config:
    EMAIL= config('EMAIL') 
    PASSKEY= config('PASSKEY')
