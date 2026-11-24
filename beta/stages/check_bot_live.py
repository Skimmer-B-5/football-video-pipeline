import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from beta.stages.telegram_bot import TelegramBotClient, get_env_credentials

token, chat_id = get_env_credentials()
bot = TelegramBotClient(token=token, default_chat_id=chat_id)

me = bot._api_call("getMe")
print("Bot user info:", me)

cmds = bot._api_call("getMyCommands")
print("Registered menu commands in Telegram:")
for c in cmds.get("result", []):
    print(f"  /{c['command']} - {c['description']}")
