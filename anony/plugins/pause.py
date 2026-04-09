# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types, F
from aiogram.filters import Command
from anony import dp, db, anon, queue
from anony.helpers import admin_check


@dp.message(Command("pause"))
@admin_check
async def pause_hndlr(m: types.Message, lang: dict):
    if not await db.get_call(m.chat.id):
        return await m.reply(lang["not_playing"])
    if await db.is_paused(m.chat.id):
        return await m.reply(lang["play_already_paused"])

    await anon.pause(m.chat.id)
    await m.reply(lang["play_paused"].format(m.from_user.mention_html()))


@dp.message(Command("resume"))
@admin_check
async def resume_hndlr(m: types.Message, lang: dict):
    if not await db.get_call(m.chat.id):
        return await m.reply(lang["not_playing"])
    if not await db.is_paused(m.chat.id):
        return await m.reply(lang["play_not_paused"])

    await anon.resume(m.chat.id)
    await m.reply(lang["play_resumed"].format(m.from_user.mention_html()))


@dp.message(Command("stop", "end"))
@admin_check
async def stop_hndlr(m: types.Message, lang: dict):
    if not await db.get_call(m.chat.id):
        return await m.reply(lang["not_playing"])

    await anon.stop(m.chat.id)
    await m.reply(lang["play_stopped"].format(m.from_user.mention_html()))


@dp.message(Command("skip", "next"))
@admin_check
async def skip_hndlr(m: types.Message, lang: dict):
    if not await db.get_call(m.chat.id):
        return await m.reply(lang["not_playing"])

    await anon.play_next(m.chat.id)
    await m.reply(lang["play_skipped"].format(m.from_user.mention_html()))

@dp.callback_query(F.data.startswith("controls "))
async def _controls_cb(query: types.CallbackQuery, lang: dict):
    data = query.data.split()
    action = data[1]
    chat_id = int(data[2])

    # Simple check for admin or auth
    if not await db.is_admin(chat_id, query.from_user.id) and not await db.is_auth(chat_id, query.from_user.id):
        return await query.answer("You are not authorized to use these controls.", show_alert=True)

    if action == "pause":
        await anon.pause(chat_id)
        await query.answer(lang["paused"])
    elif action == "resume":
        await anon.resume(chat_id)
        await query.answer(lang["playing"])
    elif action == "stop":
        await anon.stop(chat_id)
        await query.answer(lang["stopped"])
    elif action == "skip":
        await anon.play_next(chat_id)
        await query.answer(lang["skipped"])
    elif action == "replay":
        await anon.replay(chat_id)
        await query.answer(lang["replayed"])
