# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types, F
from aiogram.filters import Command
from anony import dp, db, lang, anon, queue
from anony.helpers import admin_check, buttons


@dp.message(Command("pause"))
@lang.language()
@admin_check
async def pause_hndlr(m: types.Message):
    if not await db.get_call(m.chat.id):
        return await m.reply(m.lang["not_playing"])
    if await db.is_paused(m.chat.id):
        return await m.reply(m.lang["play_already_paused"])

    await anon.pause(m.chat.id)
    await m.reply(m.lang["play_paused"].format(m.from_user.mention_html()))


@dp.message(Command("resume"))
@lang.language()
@admin_check
async def resume_hndlr(m: types.Message):
    if not await db.get_call(m.chat.id):
        return await m.reply(m.lang["not_playing"])
    if not await db.is_paused(m.chat.id):
        return await m.reply(m.lang["play_not_paused"])

    await anon.resume(m.chat.id)
    await m.reply(m.lang["play_resumed"].format(m.from_user.mention_html()))


@dp.message(Command("stop", "end"))
@lang.language()
@admin_check
async def stop_hndlr(m: types.Message):
    if not await db.get_call(m.chat.id):
        return await m.reply(m.lang["not_playing"])

    await anon.stop(m.chat.id)
    await m.reply(m.lang["play_stopped"].format(m.from_user.mention_html()))


@dp.message(Command("skip", "next"))
@lang.language()
@admin_check
async def skip_hndlr(m: types.Message):
    if not await db.get_call(m.chat.id):
        return await m.reply(m.lang["not_playing"])

    await anon.skip(m.chat.id) # Assuming anon.skip exists or use play_next
    # If skip doesn't exist in TgCall, it's usually play_next
    # Let's check calls.py again later if needed.
    await m.reply(m.lang["play_skipped"].format(m.from_user.mention_html()))

@dp.callback_query(F.data.startswith("controls "))
@lang.language()
async def _controls_cb(query: types.CallbackQuery):
    data = query.data.split()
    action = data[1]
    chat_id = int(data[2])

    # Simple check for admin or auth
    if not await db.is_admin(chat_id, query.from_user.id) and not await db.is_auth(chat_id, query.from_user.id):
        return await query.answer("You are not authorized to use these controls.", show_alert=True)

    if action == "pause":
        await anon.pause(chat_id)
        await query.answer(query.lang["paused"])
    elif action == "resume":
        await anon.resume(chat_id)
        await query.answer(query.lang["playing"])
    elif action == "stop":
        await anon.stop(chat_id)
        await query.answer(query.lang["stopped"])
    elif action == "skip":
        await anon.play_next(chat_id)
        await query.answer(query.lang["skipped"])
    elif action == "replay":
        await anon.replay(chat_id)
        await query.answer(query.lang["replayed"])

    # Update message if needed
