import os
from dotenv import load_dotenv
import questionary
import logging

def get_required_environ(name: str) -> str:
    load_dotenv()
    try:
        value = os.environ[name]
    except KeyError as e:
        logging.fatal(f"Environment variable {e} is required.")
        raise KeyError

    if len(value.strip()) == 0:
        raise ValueError(f"Required environment variable {name} cannot be empty")
    return value

#demo prototype for tty.
# not sure if this would work on window
def main():
    choices = [
        "OpenAI / GPT",
        "Anthropic / Claude",
        "HuggingFace",
        "DeepSeek"
    ]

    selected = questionary.select(
        "Choose Model Provider (use arrows):",
        choices=choices
    ).ask()

    if selected is None:
        print("Exiting...")
        return

    print(f"You selected: {selected}")

    if "OpenAI" in selected:
        key_name = "OPENAI_API_KEY"
    elif "Claude" in selected:
        key_name = "ANTHROPIC_API_KEY"
    else:
        print(f"{selected} not yet implemented.")
        return
    try:
        api_key = get_required_environ(key_name)
        print(f"{key_name} found")
        
    except (KeyError, ValueError):
        api_key = questionary.password(f"{key_name} not found. Please input API key:").ask()
        print(f"Received key: {api_key[:4]}****************")
        
    #actual api pinging should be made here.
    
    print()

if __name__ == "__main__":
    main()