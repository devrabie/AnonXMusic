# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types, F
from aiogram.filters import Command
from anony import dp, lang, db, app
from anony.helpers import reload_admins


@dp.message(Command("auth", "unauth"), F.chat.type.in_(["group", "supergroup"]))
@lang.language()
async def auth_hndlr(m: types.Message):
    # check if user is admin
    admins = await db.get_admins(m.chat.id)
    if m.from_user.id not in admins and str(m.from_user.id) != str(app.owner):
        return await m.reply(m.lang["user_no_perms"])

    command = m.text.split()
    if not m.reply_to_message and len(command) < 2:
        return await m.reply("Reply to a user or provide user ID.")

    user_id = m.reply_to_message.from_user.id if m.reply_to_message else int(command[1])

    if "un" in command[0]:
        await db.remove_auth(m.chat.id, user_id)
        await m.reply(m.lang["auth_removed"].format(user_id))
    else:
        await db.add_auth(m.chat.id, user_id)
        await m.reply(m.lang["auth_added"].format(user_id))

@dp.message(Command("reload"), F.chat.type.in_(["group", "supergroup"]))
@lang.language()
async def reload_hndlr(m: types.Message):
    await m.reply(m.lang["admin_cache_reloading"])
    admins = await reload_admins(m.chat.id)
    await db.set_admins(m.chat.id, admins)
    await m.reply(m.lang["admin_cache_reloaded"])
