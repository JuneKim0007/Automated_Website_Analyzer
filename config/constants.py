"""
Project-wide constants: API keys, model identifiers, paths.
"""

# ---- Environment variable names ----
API_KEY = "API_KEY"
ANTHROPIC_API_KEY = "ANTHROPIC_API_KEY"
OPENAI = "OPENAI"
GPT = "OPENAI"
HUGGING_FACE = "HUGGING_FACE"
HF = "HUGGING_FACE"
DEBUG = "DEBUG"
ENV = ".env"

OUTPUT_DIR = "source/analyzed_data"


# ---- Model identifiers ----
class ANTHROPIC_MODELS:
    CLAUDE_2            = "claude-2"
    CLAUDE_INSTANT      = "claude-instant"
    CLAUDE_SONNET_4_6   = "claude-sonnet-4-6"
    CLAUDE_SONNET_2_1   = "claude-sonnet-2-1"
    CLAUDE_LIGHT        = "claude-light"


class OPENAI_MODELS:
    GPT_4               = "gpt-4"
    GPT_4_32K           = "gpt-4-32k"
    GPT_3_5_TURBO       = "gpt-3.5-turbo"
    GPT_3_5_TURBO_16K   = "gpt-3.5-turbo-16k"
    TEXT_DAVINCI_003     = "text-davinci-003"


class HUGGING_FACE_MODELS:
    FLAN_T5_BASE        = "google/flan-t5-base"
    BLOOMZ_7B           = "bigscience/bloomz-7b1"
    LLAMA_2_7B          = "meta-llama/Llama-2-7b-hf"
    LLAMA_2_13B         = "meta-llama/Llama-2-13b-hf"
    LLAMA_2_70B         = "meta-llama/Llama-2-70b-hf"


class DEEP_SEEK_MODELS:
    DS_GENERIC          = "deepseek/generic"


# ---- Source directory ----
class SOURCE_DIR:
    PATH            = "PATH"
    SOURCE          = "SOURCE"
    DEFAULT_PATH    = "DEFAULT_PATH"


def env_constant_joiner(*args, sep="_") -> str:
    return sep.join(args)