import sys
from pathlib import Path

BETA_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BETA_ROOT))

from stages.telegram_bot import TelegramBotClient, get_env_credentials

token, chat_id = get_env_credentials()
bot = TelegramBotClient(token, default_chat_id=chat_id)
info = bot._api_call("getWebhookInfo")
print("Webhook info:", info)
if info.get("result", {}).get("url"):
    bot._api_call("deleteWebhook")
    print("Deleted webhook.")
else:
    print("No webhook active. Long polling is standard.")
