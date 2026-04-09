# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types, F
from aiogram.filters import Command
from anony import dp, lang, db, app, userbot


@dp.message(Command("addsudo", "rmsudo", "delsudo"), F.from_user.id == int(app.owner))
async def sudo_hndlr(m: types.Message, lang: dict):
    command = m.text.split()
    if not m.reply_to_message and len(command) < 2:
        return await m.reply("Reply to a user or provide user ID.")

    user_id = m.reply_to_message.from_user.id if m.reply_to_message else int(command[1])

    if "rm" in command[0] or "del" in command[0]:
        await db.remove_sudo(user_id)
        if user_id in app.sudoers:
            app.sudoers.remove(user_id)
        await m.reply(lang["sudo_removed"].format(user_id))
    else:
        await db.add_sudo(user_id)
        if user_id not in app.sudoers:
            app.sudoers.append(user_id)
        await m.reply(lang["sudo_added"].format(user_id))

@dp.message(Command("sudolist", "listsudo"))
async def sudolist_hndlr(m: types.Message, lang: dict):
    text = lang["sudo_owner"].format(app.owner)
    text += lang["sudo_users"]
    for count, user_id in enumerate(app.sudoers, 1):
        text += f"\n{count}. <code>{user_id}</code>"
    await m.reply(text)
