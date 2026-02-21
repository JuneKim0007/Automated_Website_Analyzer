import anthropic
import os
from env.env_loader import get_required_environ
from env.constants import API_KEY, ANTHROPIC
from env.constants import Path

def create_anthropic_client() -> anthropic.Anthropic:
    api_key = get_required_environ(AN)
    return anthropic.Anthropic(api_key=api_key)

client = create_anthropic_client()

for filename in os.listdir("."):
    if filename.endswith(".py"):
        with open(filename, "r") as f:
            content = f.read()
            
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[
                {
                    "health": "check",
                    "da" : "back",
                }
            ]
        )
