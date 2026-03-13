import os
import json

START_MSG = """👋 Welcome to Auto Unlimited Reactions Bot!

This bot adds reactions to your Telegram channel posts automatically.

━━━━━━━━━━━━━━━━━━━
📌 SETUP (one time only):
Add this bot as Admin in your channel with Edit Posts permission.

Use /help to see all commands & examples.

━━━━━━━━━━━━━━━━━━━
Made By: @SmartBoy_ApnaMS"""

HELP_MSG = """📖 BOT COMMANDS & GUIDE

━━━━━━━━━━━━━━━━━━━
1️⃣ SET BUTTON REACTIONS FOR ALL NEW POSTS:

/set_reactions --channel_id -100XXXXXXXXX --reactions 😍97 😂50 😘

👆 Every new post in your channel will auto-get these button reactions.

━━━━━━━━━━━━━━━━━━━
2️⃣ SET REAL REACTIONS ON A SPECIFIC POST:

For public channel:
/set_reactions --channel_username yourchannel --post_link https://t.me/yourchannel/19 --reactions ❤100 👍50

For private channel:
/set_reactions --channel_username 1234567890 --post_link https://t.me/c/1234567890/17 --reactions ❤100 👍50

👆 This will add real reactions on that specific post.

━━━━━━━━━━━━━━━━━━━
📌 HOW TO USE:
• For public channel: use channel username without @
• For private channel: use channel id (numbers only)
• Replace the post link with your actual post link
• Replace emojis with any reaction emoji you want
• Add count after emoji for number of reactions (e.g. ❤100)
• Reactions are unlimited

━━━━━━━━━━━━━━━━━━━
💡 HOW TO GET CHANNEL ID:
Forward any message from your channel to @userinfobot — it will show the channel ID.

━━━━━━━━━━━━━━━━━━━
⚠️ REQUIREMENTS:
• Bot must be Admin in your channel
• You must also be Admin in that channel
• Channel should be public or bot already added

━━━━━━━━━━━━━━━━━━━
Made By: @SmartBoy_ApnaMS"""

config = {
    "protected_vars": [
        "hash_salt",
        "hash_trim_bytes",
        "admin_password",
        "remembered_passwords"
    ],
    "hash_salt": os.environ.get("HASH_SALT", ""),
    "hash_bytes": int(os.environ.get("HASH_BYTES", "10")),
    "bot_token": os.environ.get("BOT_TOKEN", ""),
    "use_telegram_user_api": os.environ.get("USE_TELEGRAM_USER_API", "false").lower() == "true",
    "use_native_reactions": os.environ.get("USE_NATIVE_REACTIONS", "false").lower() == "true",
    "telegram_api_session": os.environ.get("TELEGRAM_API_SESSION", "liker"),
    "telegram_api_id": int(os.environ.get("TELEGRAM_API_ID", "0")),
    "telegram_api_hash": os.environ.get("TELEGRAM_API_HASH", ""),
    "admin_password": os.environ.get("ADMIN_PASSWORD", ""),
    "remembered_passwords": {},
    "enable_only_for": [],
    "last_reactions": int(os.environ.get("LAST_REACTIONS", "1000000")),
    "last_reactions_save_seconds": int(os.environ.get("LAST_REACTIONS_SAVE_SECONDS", "100")),
    "channel_rate_per_minute": int(os.environ.get("CHANNEL_RATE_PER_MINUTE", "20")),
    "channel_rate_min_seconds": int(os.environ.get("CHANNEL_RATE_MIN_SECONDS", "1")),
    "global_rate_per_second": int(os.environ.get("GLOBAL_RATE_PER_SECOND", "30")),
    "reply_markup_trail": int(os.environ.get("REPLY_MARKUP_TRAIL", "100")),
    "comment_trail": int(os.environ.get("COMMENT_TRAIL", "100")),
    "channel_state_save_seconds": int(os.environ.get("CHANNEL_STATE_SAVE_SECONDS", "2")),
    "response_start": START_MSG,
    "response_help": HELP_MSG,
    "response_reaction_added": os.environ.get("RESPONSE_REACTION_ADDED", "{}"),
    "response_reaction_removed": os.environ.get("RESPONSE_REACTION_REMOVED", "{} removed"),
    "response_command_parser_error": os.environ.get("RESPONSE_COMMAND_PARSER_ERROR", "Unknown or incomplete command {command}"),
    "response_unknown_command": os.environ.get("RESPONSE_UNKNOWN_COMMAND", "Unknown or incomplete command {command}")
}

os.makedirs("data", exist_ok=True)

with open("data/config.json", "w") as f:
    json.dump(config, f, indent=2)

print("✅ config.json generated successfully from environment variables!")
