# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import asyncio
import signal
import importlib
from contextlib import suppress

from anony import (anon, app, dp, config, db, logger,
                   stop, thumb, userbot, yt)
from anony.plugins import all_modules

async def main():
    await db.connect()
    await app.boot()
    await userbot.boot()
    await anon.boot()
    await thumb.start()

    for module in all_modules:
        importlib.import_module(f"anony.plugins.{module}")
    logger.info(f"Loaded {len(all_modules)} modules.")

    if config.COOKIES_URL:
        await yt.save_cookies(config.COOKIES_URL)

    # sudoers and blacklisted users are now part of the FSM or Filter logic
    # but let's keep the memory sets updated if plugins use them.
    sudoers = await db.get_sudoers()
    app.sudoers = sudoers # Assuming Bot class was updated or we use db directly
    db.blacklisted = await db.get_blacklisted()
    logger.info(f"Loaded {len(sudoers)} sudo users.")

    try:
        await dp.start_polling(app)
    finally:
        await stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
