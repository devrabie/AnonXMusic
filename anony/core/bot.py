# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import logging
from aiogram import Bot as AiogramBot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatMemberStatus

from anony import config, logger


class Bot(AiogramBot):
    def __init__(self):
        super().__init__(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.owner = config.OWNER_ID
        self.logger_id = config.LOGGER_ID

    async def boot(self):
        """
        Starts the bot and performs initial setup.
        """
        self.me = await self.get_me()
        self.id = self.me.id
        self.name = self.me.first_name
        self.username = self.me.username
        self.mention = f"@{self.username}"

        try:
            await self.send_message(self.logger_id, "Bot Started")
            get = await self.get_chat_member(self.logger_id, self.id)
            if get.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                logger.warning("Please promote the bot as an admin in logger group.")
        except Exception as ex:
            logger.warning(f"Bot has failed to access the log group: {self.logger_id}\nReason: {ex}")
        logger.info(f"Bot started as @{self.username}")

    async def exit(self):
        """
        Asynchronously stops the bot.
        """
        await self.session.close()
        logger.info("Bot stopped.")
