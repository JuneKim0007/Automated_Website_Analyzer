
API_KEY = "API_KEY"
ANTHROPIC_API_KEY = "ANTHROPIC_API_KEY"
OPENAI = "OPENAI"
GPT = "OPENAI"
HUGGING_FACE = "HUGGING_FACE"
HF = "HUGGING_FACE" # alais for Hugging Face
DEBUG = "DEBUG"
ENV = ".env"

class ANTHROPIC_MODELS:
    CLAUDE_SONNET_4_6 = "claude-sonnet-4-6"


# -----------------------------
# Source directories / constants
# -----------------------------
class SOURCE_DIR:
    PATH = "PATH"
    SOURCE = "SOURCE"
    DEFAULT_PATH = "DEFAULT_PATH"


# -----------------------------
# Model identifiers / constants
# -----------------------------
class ANTHROPIC_MODELS:
    # Generic / widely used first
    CLAUDE_2 = "claude-2"
    CLAUDE_INSTANT = "claude-instant"
    CLAUDE_SONNET_4_6 = "claude-sonnet-4-6"
    CLAUDE_SONNET_2_1 = "claude-sonnet-2-1"
    CLAUDE_LIGHT = "claude-light"


class OPENAI_MODELS:
    # Generic / widely used first
    GPT_4 = "gpt-4"
    GPT_4_32K = "gpt-4-32k"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_3_5_TURBO_16K = "gpt-3.5-turbo-16k"
    TEXT_DAVINCI_003 = "text-davinci-003"
    TEXT_DAVINCI_002 = "text-davinci-002"
    CODE_DAVINCI_002 = "code-davinci-002"


class HUGGING_FACE_MODELS:
    # Generic / widely used first
    FLAN_T5_BASE = "google/flan-t5-base"
    BLOOMZ_7B = "bigscience/bloomz-7b1"
    BLOOM_176B = "bigscience/bloom"
    LLAMA_2_7B = "meta-llama/Llama-2-7b-hf"
    LLAMA_2_13B = "meta-llama/Llama-2-13b-hf"
    LLAMA_2_70B = "meta-llama/Llama-2-70b-hf"
    OPT_6_7B = "facebook/opt-6.7b"
    OPT_13B = "facebook/opt-13b"


class DEEP_SEEK_MODELS:
    # Generic / widely used first
    DS_GENERIC = "deepseek/generic"
    DS_MODEL_1 = "deepseek/model-1"
    DS_MODEL_2 = "deepseek/model-2"
    DS_MODEL_3 = "deepseek/model-3"
    DS_MODEL_4 = "deepseek/model-4"
    DS_MODEL_5 = "deepseek/model-5"
#join the constant;.
def env_constant_joiner(*args, sep= "_") -> str:
    return sep.join(args)