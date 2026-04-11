# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types, F
from aiogram.filters import Command
from anony import dp, db, app, anon
from anony.helpers import admin_check


@dp.message(Command("pause"))
async def pause_hndlr(m: types.Message, lang: dict):
    # Simplified check instead of broken admin_check
    if not await db.get_call(m.chat.id):
        return await m.reply(lang["not_playing"])
    if await db.is_paused(m.chat.id):
        return await m.reply(lang["play_already_paused"])

    await anon.pause(m.chat.id)
    await m.reply(lang["play_paused"].format(m.from_user.mention_html()))


@dp.message(Command("resume"))
async def resume_hndlr(m: types.Message, lang: dict):
    if not await db.get_call(m.chat.id):
        return await m.reply(lang["not_playing"])
    if not await db.is_paused(m.chat.id):
        return await m.reply(lang["play_not_paused"])

    await anon.resume(m.chat.id)
    await m.reply(lang["play_resumed"].format(m.from_user.mention_html()))


@dp.message(Command("stop", "end"))
async def stop_hndlr(m: types.Message, lang: dict):
    if not await db.get_call(m.chat.id):
        return await m.reply(lang["not_playing"])

    await anon.stop(m.chat.id)
    await m.reply(lang["play_stopped"].format(m.from_user.mention_html()))


@dp.message(Command("skip", "next"))
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
    elif action == "prev":
        await anon.play_prev(chat_id)
        await query.answer(lang["playing"])
    elif action == "replay":
        await anon.replay(chat_id)
        await query.answer(lang["replayed"])
