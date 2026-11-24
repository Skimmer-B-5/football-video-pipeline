import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from beta.stages.telegram_bot import TelegramBotClient, get_env_credentials

token, chat_id = get_env_credentials()
bot = TelegramBotClient(token=token, default_chat_id=chat_id)

reply_markup = {
    "inline_keyboard": [
        [
            {"text": "⭐ Endrick to Milan (€60M)", "callback_data": "retro_endrick_milan"},
            {"text": "🔥 Gyökeres to Arsenal (€75M)", "callback_data": "retro_gyokeres_arsenal"}
        ],
        [
            {"text": "⚡ Davies to Real Madrid (€45M)", "callback_data": "retro_davies_madrid"},
            {"text": "🎯 Rodri to Real Madrid (€150M)", "callback_data": "retro_rodri_madrid"}
        ]
    ]
}

welcome_text = (
    "📺 <b>1990s TELEVISION BROADCAST STUDIO IS LIVE! (V7.1.6.7)</b>\n\n"
    "<i>The master 90s television broadcast pipeline has been loaded without retiring existing tools. You can now create videos directly from your phone!</i>\n\n"
    "<b>New Commands:</b>\n"
    "• <b>/broadcast [story]</b> — <i>Generate a 30s broadcast short (e.g. <code>/broadcast Gyokeres to Arsenal</code>)</i>\n"
    "• <b>/retro</b> — <i>Interactive menu to select or generate a 90s TV news bulletin</i>\n\n"
    "<i>Preserved Existing Commands:</i>\n"
    "• <b>/new</b> — <i>Legacy trending stories cycle</i>\n"
    "• <b>/chat [question]</b> — <i>Debate tactics with Qwen</i>\n"
    "• <b>/search [query]</b> — <i>Search live web news</i>\n\n"
    "<b>Tap below to generate a video right now:</b>"
)

res = bot.send_message(welcome_text, reply_markup=reply_markup, chat_id=chat_id)
print(f"Dispatched welcome menu! Message ID: {res}")
