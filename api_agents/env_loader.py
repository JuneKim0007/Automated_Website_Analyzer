import logging
from os import environ
from dotenv import load_dotenv

def get_required_environ(name: str) -> str:
    load_dotenv()
    try:
        value = environ[name]
    except KeyError as e:
        logging.fatal(f"Environment variable {e} is required.")
        raise KeyError

    if len(value.strip()) == 0:
        raise ValueError(f"Required environment variable {name} cannot be empty")
    return value
