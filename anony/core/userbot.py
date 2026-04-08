# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import Client

from anony import config, logger


class Userbot(Client):
    def __init__(self):
        """
        Initializes the userbot with multiple clients.

        This method sets up clients for the userbot using predefined session strings.
        Each client is assigned a unique name based on the key in the `clients` dictionary.
        """
        self.clients = []

    async def _init_client(self, key: str, session: str):
        """Initializes a single userbot client."""
        from anony import db
        if not session:
            session = await db.get_session(key)

        if not session:
            return

        name = f"AnonyUB{key[-1]}"
        setattr(
            self,
            key,
            Client(
                name=name,
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                session_string=session,
            ),
        )

    async def boot_client(self, num: int, ub: Client):
        """
        Boot a client and perform initial setup.
        Args:
            num (int): The client number to boot (1, 2, or 3).
            ub (Client): The userbot client instance.
        Raises:
            SystemExit: If the client fails to send a message in the log group.
        """
        await ub.start()
        try:
            await ub.send_message(config.LOGGER_ID, "Assistant Started")
        except Exception:
            logger.warning(f"Assistant {num} failed to send message in log group.")

        ub.id = ub.me.id
        ub.name = ub.me.first_name
        ub.username = ub.me.username
        ub.mention = ub.me.mention
        self.clients.append(ub)
        try:
            await ub.join_chat("fallenx")
        except Exception:
            pass
        logger.info(f"Assistant {num} started as @{client.username}")

    async def boot(self):
        """
        Asynchronously starts the assistants.
        """
        await self._init_client("one", config.SESSION1)
        await self._init_client("two", config.SESSION2)
        await self._init_client("three", config.SESSION3)

        if hasattr(self, "one"):
            await self.boot_client(1, self.one)
        if hasattr(self, "two"):
            await self.boot_client(2, self.two)
        if hasattr(self, "three"):
            await self.boot_client(3, self.three)

    async def exit(self):
        """
        Asynchronously stops the assistants.
        """
        if hasattr(self, "one"):
            await self.one.stop()
        if hasattr(self, "two"):
            await self.two.stop()
        if hasattr(self, "three"):
            await self.three.stop()
        logger.info("Assistants stopped.")
