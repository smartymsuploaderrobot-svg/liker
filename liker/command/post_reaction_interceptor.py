import re
import logging
import inject
from tengi.telegram.inbox_handler import *
from tengi import Config, TelegramBot

from liker.command.handler_post_reaction import (
    parse_reaction_with_count,
    extract_message_id_from_link,
    resolve_chat_id,
    send_reactions_to_post
)

logger = logging.getLogger(__file__)


class PostReactionInterceptor(TelegramInboxHandler):
    """
    Intercepts /set_reactions commands with channel_username and post link
    before the standard CommandParser sees them. This handles the user's
    preferred format with spaces (e.g. '--post link') that argparse cannot parse.
    """
    config = inject.attr(Config)
    telegram_bot = inject.attr(TelegramBot)

    def message(self, message: types.Message) -> bool:
        if message.text is None:
            return False

        text = message.text.strip()

        if not text.startswith('/set_reactions'):
            return False

        normalized = text.replace('\u2014', '--').replace('\u2013', '--')

        if 'channel_username' not in normalized.lower():
            return False

        try:
            normalized = re.sub(r'--\s+', '--', normalized)
            normalized = re.sub(r'--post[\s_]+link\b', '--post_link', normalized, flags=re.IGNORECASE)

            ch_match = re.search(r'--channel_username\s+(\S+)', normalized)
            if not ch_match:
                self.telegram_bot.bot.send_message(
                    message.chat.id,
                    'Missing channel_username parameter'
                )
                return True
            channel_username = ch_match.group(1)

            link_match = re.search(r'--post_link\s+(https?://\S+)', normalized)
            if not link_match:
                self.telegram_bot.bot.send_message(
                    message.chat.id,
                    'Missing post_link parameter. Provide a valid Telegram post URL.'
                )
                return True
            post_link = link_match.group(1)

            react_match = re.search(r'--reactions?\s+(.+)$', normalized)
            if not react_match:
                self.telegram_bot.bot.send_message(
                    message.chat.id,
                    'Missing reactions parameter'
                )
                return True
            reactions_str = react_match.group(1).strip()

            tokens = reactions_str.split()
            reactions = []
            i = 0
            while i < len(tokens):
                token = tokens[i]
                if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                    reactions.append(token + tokens[i + 1])
                    i += 2
                else:
                    reactions.append(token)
                    i += 1

            message_id = extract_message_id_from_link(post_link)
            if message_id is None:
                self.telegram_bot.bot.send_message(
                    message.chat.id,
                    'Invalid post link format. Use: https://t.me/channel/123'
                )
                return True

            chat_id = resolve_chat_id(channel_username)

            reactions_parsed = []
            for r in reactions:
                emoji, count = parse_reaction_with_count(r)
                if emoji:
                    reactions_parsed.append((emoji, count))

            if not reactions_parsed:
                self.telegram_bot.bot.send_message(
                    message.chat.id,
                    'No valid reactions provided'
                )
                return True

            bot_token = self.config['bot_token']
            success, result_msg = send_reactions_to_post(
                bot_token=bot_token,
                chat_id=chat_id,
                message_id=message_id,
                reactions_list=reactions_parsed
            )

            if success:
                reactions_summary = ', '.join(
                    [f'{emoji}{count}' for emoji, count in reactions_parsed]
                )
                self.telegram_bot.bot.send_message(
                    message.chat.id,
                    f'Reactions {reactions_summary} sent to post {post_link}'
                )
            else:
                self.telegram_bot.bot.send_message(
                    message.chat.id,
                    f'Failed to send reactions: {result_msg}'
                )

            return True

        except Exception as ex:
            logger.exception(f'Error in PostReactionInterceptor: {ex}')
            self.telegram_bot.bot.send_message(
                message.chat.id,
                f'Error processing command: {str(ex)}'
            )
            return True
