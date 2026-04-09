# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import time
import asyncio
import logging
import pyrogram.errors
from logging.handlers import RotatingFileHandler
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Monkeypatch for compatibility with pytgcalls and different pyrogram versions
if not hasattr(pyrogram.errors, "GroupcallForbidden"):
    class GroupcallForbidden(pyrogram.errors.Forbidden):
        pass
    pyrogram.errors.GroupcallForbidden = GroupcallForbidden

logging.basicConfig(
    format="[%(asctime)s - %(levelname)s] - %(name)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("log.txt", maxBytes=10485760, backupCount=5),
        logging.StreamHandler(),
    ],
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("ntgcalls").setLevel(logging.CRITICAL)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pytgcalls").setLevel(logging.ERROR)
logging.getLogger("aiogram").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


__version__ = "3.0.2"

from config import Config

config = Config()
config.check()
tasks = []
boot = time.time()

from anony.core.bot import Bot
app = Bot()
dp = Dispatcher(storage=MemoryStorage())

# Register Middleware
from anony.core.middleware import LanguageMiddleware
dp.message.middleware(LanguageMiddleware())
dp.callback_query.middleware(LanguageMiddleware())

from anony.core.dir import ensure_dirs
ensure_dirs()

from anony.core.userbot import Userbot
userbot = Userbot()

from anony.core.database import Database
db = Database()

from anony.core.lang import Language
lang = Language()

from anony.core.telegram import Telegram
from anony.core.youtube import YouTube
tg = Telegram()
yt = YouTube()

from anony.helpers import Queue, Thumbnail
queue = Queue()
thumb = Thumbnail()

from anony.core.calls import TgCall
anon = TgCall()


async def stop() -> None:
    logger.info("Stopping...")
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.exceptions.CancelledError:
            pass

    await app.exit()
    await userbot.exit()
    await db.close()
    await thumb.close()

    logger.info("Stopped.\n")
