# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import asyncio
from aiogram import types, F, enums
from aiogram.filters import Command

from anony import app, dp, config, db, userbot
from anony.helpers import buttons, utils


@dp.message(Command("help"), F.chat.type == enums.ChatType.PRIVATE)
async def _help(m: types.Message, lang: dict):
    await m.reply(
        text=lang["help_menu"],
        reply_markup=buttons.help_markup(lang),
    )


@dp.message(Command("start"))
async def start(message: types.Message, lang: dict):
    command = message.text.split()
    if len(command) > 1 and command[1] == "help":
        return await _help(message, lang)

    private = message.chat.type == enums.ChatType.PRIVATE
    _text = (
        lang["start_pm"].format(message.from_user.first_name, app.name)
        if private
        else lang["start_gp"].format(app.name)
    )

    key = buttons.start_key(lang, private, message.from_user.id)
    await message.reply(
        text=_text,
        reply_markup=key,
    )

    if private:
        if await db.is_user(message.from_user.id):
            return
        await utils.send_log(message)
        await db.add_user(message.from_user.id)
    else:
        if not await db.is_chat(message.chat.id):
            await utils.send_log(message, True)
            await db.add_chat(message.chat.id, message.from_user.id)


@dp.message(Command("playmode", "settings"), F.chat.type.in_([enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]))
async def settings(message: types.Message, lang: dict):
    admin_only = await db.get_play_mode(message.chat.id)
    cmd_delete = await db.get_cmd_delete(message.chat.id)
    _language = await db.get_lang(message.chat.id)
    await message.reply(
        text=lang["start_settings"].format(message.chat.title),
        reply_markup=buttons.settings_markup(
            lang, admin_only, cmd_delete, _language, message.chat.id
        ),
    )

@dp.my_chat_member()
async def _bot_member_update(update: types.ChatMemberUpdated, lang: dict):
    if update.new_chat_member.status == enums.ChatMemberStatus.ADMINISTRATOR:
        if not await db.is_chat(update.chat.id):
            user_id = update.from_user.id if update.from_user else None
            await db.add_chat(update.chat.id, user_id)
            await update.bot.send_message(
                update.chat.id,
                lang["chat_added"].format(update.chat.title)
            )

        # Assistant join logic
        try:
            client = await db.get_assistant(update.chat.id)
            if client:
                try:
                    await client.get_chat_member(update.chat.id, client.id)
                except Exception:
                    chat = await update.bot.get_chat(update.chat.id)
                    if chat.username:
                        invite_link = chat.username
                    else:
                        invite_link = chat.invite_link or await update.bot.export_chat_invite_link(update.chat.id)
                    await client.join_chat(invite_link)
        except Exception:
            pass

@dp.message(F.new_chat_members)
async def _new_member(message: types.Message, lang: dict):
    await asyncio.sleep(3)
    for member in message.new_chat_members:
        if member.id == app.id:
            if not await db.is_chat(message.chat.id):
                user_id = message.from_user.id if message.from_user else None
                await utils.send_log(message, True)
                await db.add_chat(message.chat.id, user_id)
            await message.reply(lang["promote_me"])
