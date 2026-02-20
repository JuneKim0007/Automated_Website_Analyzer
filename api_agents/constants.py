
API_KEY = "API_KEY"
ANTHROPIC = "ANTHROPIC"
CLAUDE = "ANTHROPIC" # alias for Anthropic
OPENAI = "OPENAI"
GPT = "OPENAI"
HUGGING_FACE = "HUGGING_FACE"
HF = "HUGGING_FACE" # alais for Hugging Face
DEBUG = "DEBUG"
ENV = ".env"

class SOURCE_DIR():
    PATH= "PATH"
    SOURCE = "SOURCE"
    DEFAULT_PATH = "DEFAULT_PATH"

#join the constant;.
def env_constant_joiner(*args, sep= "_") -> str:
    return sep.join(args)
