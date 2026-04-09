# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from functools import wraps
from aiogram import types, enums

from anony import app, db


def admin_check(func):
    @wraps(func)
    async def wrapper(update: types.Message | types.CallbackQuery, lang: dict, *args, **kwargs):
        async def reply(text):
            if isinstance(update, types.Message):
                return await update.reply(text)
            else:
                return await update.answer(text, show_alert=True)

        chat = (
            update.chat
            if isinstance(update, types.Message)
            else update.message.chat
        )
        if chat.type == enums.ChatType.PRIVATE:
            return await func(update, lang, *args, **kwargs)

        user_id = update.from_user.id
        admins = await db.get_admins(chat.id)

        if user_id == int(app.owner):
            return await func(update, lang, *args, **kwargs)

        if user_id not in admins:
            if not admins:
                admins = await reload_admins(chat.id)
                await db.set_admins(chat.id, admins)

            if user_id not in admins:
                return await reply(lang["user_no_perms"])

        return await func(update, lang, *args, **kwargs)

    return wrapper


def can_manage_vc(func):
    @wraps(func)
    async def wrapper(update: types.Message | types.CallbackQuery, lang: dict, *args, **kwargs):
        chat_id = (
            update.chat.id
            if isinstance(update, types.Message)
            else update.message.chat.id
        )
        user_id = update.from_user.id

        if user_id == int(app.owner):
            return await func(update, lang, *args, **kwargs)

        if await db.is_auth(chat_id, user_id):
            return await func(update, lang, *args, **kwargs)

        admins = await db.get_admins(chat_id)
        if user_id in admins:
            return await func(update, lang, *args, **kwargs)

        if isinstance(update, types.Message):
            return await update.reply(lang["user_no_perms"])
        else:
            return await update.answer(lang["user_no_perms"], show_alert=True)

    return wrapper


async def is_admin(chat_id: int, user_id: int) -> bool:
    if user_id in await db.get_admins(chat_id):
        return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.CREATOR,
        ]
    except Exception:
        return False


async def reload_admins(chat_id: int) -> list[int]:
    try:
        admins = await app.get_chat_administrators(chat_id)
        return [admin.user.id for admin in admins if not admin.user.is_bot]
    except Exception:
        return []
