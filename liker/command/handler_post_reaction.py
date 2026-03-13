import re
import inject
import logging
import requests
from tengi.command.command_handler import *
from tengi import Config, TelegramBot

logger = logging.getLogger(__file__)


def parse_reaction_with_count(reaction_str):
    """Parse a reaction string like '❤100' into (emoji, count) tuple."""
    emoji = reaction_str
    count_str = ''
    while emoji and emoji[-1].isdigit():
        count_str = emoji[-1] + count_str
        emoji = emoji[:-1]
    count = int(count_str) if count_str else 1
    return emoji, count


def extract_message_id_from_link(post_link):
    """Extract message_id from a Telegram post link.

    Supports:
        https://t.me/channelname/123
        https://t.me/c/1234567890/123
    """
    match = re.search(r'/(\d+)\s*$', post_link.strip())
    if match:
        return int(match.group(1))
    return None


def resolve_chat_id(channel_username):
    """Resolve chat_id from channel_username.

    For public channels: username string -> @username
    For private channels: numeric string -> -100XXXX format
    """
    clean = channel_username.strip().lstrip('@')

    if clean.lstrip('-').isdigit():
        numeric_val = clean if clean.startswith('-') else clean
        if numeric_val.startswith('-'):
            return int(numeric_val)
        elif numeric_val.startswith('100'):
            return int(f'-{numeric_val}')
        else:
            return int(f'-100{numeric_val}')
    else:
        return f'@{clean}'


def send_reactions_to_post(bot_token, chat_id, message_id, reactions_list):
    """Send real Telegram reactions to a specific post using Bot API.

    Args:
        bot_token: The bot's API token
        chat_id: Channel ID (int) or @username (str)
        message_id: The message ID to react to
        reactions_list: List of (emoji, count) tuples

    Returns:
        (success, message) tuple
    """
    url = f"https://api.telegram.org/bot{bot_token}/setMessageReaction"

    reaction_objects = []
    for emoji, count in reactions_list:
        reaction_objects.append({
            "type": "emoji",
            "emoji": emoji
        })

    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reaction": reaction_objects,
        "is_big": True
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()

        if result.get('ok'):
            return True, "Reactions sent successfully"
        else:
            error_desc = result.get('description', 'Unknown error')
            return False, f"Telegram API error: {error_desc}"
    except requests.RequestException as ex:
        return False, f"Request failed: {str(ex)}"


class CommandHandlerPostReaction(CommandHandler):
    config = inject.attr(Config)
    telegram_bot = inject.attr(TelegramBot)

    def get_cards(self) -> Iterable[CommandCard]:
        return []

    def handle(self, context: CommandContext):
        pass

    def handle_post_reaction(self, context: CommandContext,
                             channel_username: str,
                             post_link: str,
                             reactions: list):
        """Handle sending real reactions to a specific post.

        Args:
            context: The command context
            channel_username: Channel username (public) or channel ID (private)
            post_link: Telegram post link
            reactions: List of reaction strings like ['❤100', '👍50']
        """
        message_id = extract_message_id_from_link(post_link)
        if message_id is None:
            context.reply('Invalid post link. Use format: https://t.me/channel/123',
                          log_level=logging.INFO)
            return

        chat_id = resolve_chat_id(channel_username)

        reactions_parsed = []
        for r in reactions:
            emoji, count = parse_reaction_with_count(r)
            if emoji:
                reactions_parsed.append((emoji, count))

        if not reactions_parsed:
            context.reply('No valid reactions provided.',
                          log_level=logging.INFO)
            return

        bot_token = self.config['bot_token']

        success, message = send_reactions_to_post(
            bot_token=bot_token,
            chat_id=chat_id,
            message_id=message_id,
            reactions_list=reactions_parsed
        )

        if success:
            reactions_summary = ', '.join(
                [f'{emoji}{count}' for emoji, count in reactions_parsed]
            )
            context.reply(
                f'Reactions {reactions_summary} sent to post {post_link}',
                log_level=logging.INFO
            )
        else:
            context.reply(f'Failed to send reactions: {message}',
                          log_level=logging.INFO)
