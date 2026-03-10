import logging
import inject
import requests
from typing import Optional, List, Tuple
from telebot.apihelper import ApiTelegramException
from tengi import Config, telegram_bot_utils, TelegramBot, ReplyContext

from liker.state.enabled_channels import EnabledChannels

logger = logging.getLogger(__file__)


def _set_native_reactions_api(bot_token: str, chat_id, message_id: int, reactions: List[str]):
    """
    Call Telegram setMessageReaction directly (real reactions, not inline buttons).
    The bot seeds each emoji as a native reaction on the post.
    """
    url = f"https://api.telegram.org/bot{bot_token}/setMessageReaction"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reaction": [{"type": "emoji", "emoji": r} for r in reactions],
        "is_big": True
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if not data.get('ok'):
            logger.warning(f'setMessageReaction failed: {data}')
        return data.get('ok', False)
    except Exception as ex:
        logger.error(f'setMessageReaction error: {ex}')
        return False


class EnablingManager:
    config = inject.attr(Config)
    telegram_bot = inject.attr(TelegramBot)
    enabled_channels = inject.attr(EnabledChannels)

    def try_set_reactions(self,
                          channel_id,
                          reactions: list,
                          reply_context: ReplyContext,
                          sender_id_to_check: Optional[int]) -> bool:
        enable_only_for = self.config['enable_only_for']
        if enable_only_for and (telegram_bot_utils.to_int_chat_id_if_possible(channel_id) not in enable_only_for):
            reply_context.reply(f'Cannot enable for channel {channel_id}')
            return False

        try:
            channel_info = self.telegram_bot.bot.get_chat(channel_id)

            if sender_id_to_check is not None:
                channel_admins = self.telegram_bot.bot.get_chat_administrators(channel_id)
                sender_is_admin = any([a.user.id == sender_id_to_check for a in channel_admins])
                if not sender_is_admin:
                    reply_context.reply(
                        'Cannot set reactions for the given chat as the sender is not an admin in there',
                        log_level=logging.INFO)
                    return False
        except ApiTelegramException:
            logging.info('Cannot get channel info, bot is not an admin in there')
            reply_context.reply(f'Add bot as an administrator to {channel_id}')
            return False

        channel_id_int = channel_info.id
        linked_chat_id = channel_info.linked_chat_id
        self.enabled_channels.update_channel_dict(str_channel_id=str(channel_id_int),
                                                  reactions=reactions,
                                                  linked_chat_id=linked_chat_id)
        return True

    def apply_reactions_to_post(self,
                                channel_id,
                                message_id: int,
                                reactions_with_counts: List[Tuple[str, int]],
                                reply_context: ReplyContext,
                                sender_id_to_check: Optional[int]) -> bool:
        """
        Apply reactions with specific counts to a specific post.
        Uses inline keyboard buttons so counters can be pre-set.
        """
        from liker.custom_markup import markup_utils
        from liker.setup import constants

        try:
            channel_info = self.telegram_bot.bot.get_chat(channel_id)

            if sender_id_to_check is not None:
                channel_admins = self.telegram_bot.bot.get_chat_administrators(channel_id)
                sender_is_admin = any([a.user.id == sender_id_to_check for a in channel_admins])
                if not sender_is_admin:
                    reply_context.reply(
                        'You must be an admin in that channel to apply reactions.',
                        log_level=logging.INFO)
                    return False
        except ApiTelegramException:
            reply_context.reply(f'Add bot as an administrator to {channel_id}')
            return False

        channel_id_int = channel_info.id

        # Build markup with initial counts
        reply_markup = markup_utils.extend_reply_markup_with_counts(
            reactions_with_counts=reactions_with_counts,
            handler=constants.CHANNEL_POST_HANDLER,
            case_id=''
        )

        try:
            self.telegram_bot.bot.edit_message_reply_markup(
                chat_id=channel_id_int,
                message_id=message_id,
                reply_markup=reply_markup
            )
            logger.info(f'Applied reactions to post {message_id} in {channel_id_int}')
            return True
        except ApiTelegramException as ex:
            logger.error(f'Failed to edit message markup: {ex}')
            reply_context.reply(f'Failed to apply reactions: {ex}')
            return False

    def seed_native_reactions(self, channel_id: int, message_id: int, reactions: List[str]):
        """
        Seed real Telegram native reactions on a post using setMessageReaction.
        Bot adds its own reaction — users can then add theirs naturally.
        """
        bot_token = self.config['bot_token']
        ok = _set_native_reactions_api(
            bot_token=bot_token,
            chat_id=channel_id,
            message_id=message_id,
            reactions=reactions
        )
        if ok:
            logger.info(f'Native reactions seeded on {channel_id}/{message_id}: {reactions}')
        return ok

