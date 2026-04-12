# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import logging
from aiogram import Bot as AiogramBot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode, ChatMemberStatus

from anony import config, logger


class Bot(AiogramBot):
    def __init__(self):
        session = None
        if config.API_SERVER:
            from aiogram.client.session.aiohttp import AiohttpSession
            server = TelegramAPIServer.from_base(config.API_SERVER)
            session = AiohttpSession(api=server)

        super().__init__(
            token=config.BOT_TOKEN,
            session=session,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.owner = config.OWNER_ID
        self.logger_id = config.LOGGER_ID
        self.sudoers = [int(self.owner)]

    @property
    def name(self):
        return self._me.first_name

    @property
    def username(self):
        return self._me.username

    @property
    def mention(self):
        return f"@{self.username}"

    async def boot(self):
        """
        Starts the bot and performs initial setup.
        """
        self._me = await self.get_me()
        self.id = self._me.id

        if config.API_SERVER:
            logger.info(f"Using Local API Server: {config.API_SERVER}")

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
