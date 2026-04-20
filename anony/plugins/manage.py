# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import asyncio
from aiogram import types, F, enums
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from anony import app, dp, db, lang, anon, tg, queue
from anony.helpers import buttons

class ManageChat(StatesGroup):
    entering_url = State()
    entering_chat_id = State()
    entering_tg_link = State()

@dp.message(Command("manage", "dashboard"), F.chat.type == enums.ChatType.PRIVATE)
async def _dashboard(m: types.Message, lang: dict):
    chats = await db.get_chats(user_id=m.from_user.id)
    if not chats:
        return await m.reply(
            text=lang["no_chats"],
            reply_markup=buttons.dashboard_markup(lang, [])
        )

    chat_list = []
    for chat_id in chats:
        try:
            chat = await app.get_chat(chat_id)
            chat_list.append((chat_id, chat.title))
        except Exception:
            continue

    await m.reply(
        text=lang["manage_chats"],
        reply_markup=buttons.dashboard_markup(lang, chat_list)
    )

@dp.callback_query(F.data == "manage_chats")
async def _manage_chats_cb(query: types.CallbackQuery, lang: dict):
    chats = await db.get_chats(user_id=query.from_user.id)
    if not chats:
        return await query.message.edit_text(
            text=lang["no_chats"],
            reply_markup=buttons.dashboard_markup(lang, [])
        )

    chat_list = []
    for chat_id in chats:
        try:
            chat = await app.get_chat(chat_id)
            chat_list.append((chat_id, chat.title))
        except Exception:
            continue

    await query.message.edit_text(
        text=lang["manage_chats"],
        reply_markup=buttons.dashboard_markup(lang, chat_list)
    )

@dp.callback_query(F.data.regexp(r"manage_chat (-?\d+)"))
async def _manage_chat(query: types.CallbackQuery, lang: dict):
    chat_id = int(query.data.split()[1])
    url, status, stype, source = await db.get_stream(chat_id)

    # Check if currently playing
    is_playing = await db.get_call(chat_id)

    if is_playing:
        keyboard = buttons.controls(chat_id)
    else:
        keyboard = buttons.stream_markup(lang, chat_id, status, stype, source)

    await query.message.edit_text(
        text=lang["stream_settings"].format(chat_id),
        reply_markup=keyboard
    )

@dp.callback_query(F.data.regexp(r"toggle_stype (-?\d+)"))
async def _toggle_stype(query: types.CallbackQuery, lang: dict):
    chat_id = int(query.data.split()[1])
    url, status, stype, source = await db.get_stream(chat_id)

    new_type = "video" if stype == "audio" else "audio"
    await db.set_stream(chat_id, stype=new_type)
    await _manage_chat(query)

@dp.callback_query(F.data.regexp(r"set_url (-?\d+)"))
async def _set_url_prompt(query: types.CallbackQuery, state: FSMContext, lang: dict):
    chat_id = int(query.data.split()[1])
    await state.update_data(chat_id=chat_id, last_msg=query.message.message_id)
    await state.set_state(ManageChat.entering_url)
    await query.message.edit_text(
        lang["enter_url"],
        reply_markup=buttons.cancel_markup(lang)
    )
    await query.answer()

@dp.message(ManageChat.entering_url)
async def _process_url(m: types.Message, state: FSMContext, lang: dict):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    url = m.text
    await db.set_stream(chat_id, url=url)

    # Clean up previous messages
    try:
        await m.bot.delete_message(m.chat.id, data.get("last_msg"))
    except:
        pass

    await m.reply(lang["url_set"])
    await state.clear()

@dp.callback_query(F.data == "add_chat_manual")
async def _add_chat_manual_prompt(query: types.CallbackQuery, state: FSMContext, lang: dict):
    await state.update_data(last_msg=query.message.message_id)
    await state.set_state(ManageChat.entering_chat_id)
    await query.message.edit_text(
        lang["enter_chat_id"],
        reply_markup=buttons.cancel_markup(lang)
    )
    await query.answer()

@dp.message(ManageChat.entering_chat_id)
async def _process_chat_id(m: types.Message, state: FSMContext, lang: dict):
    data = await state.get_data()
    chat_input = m.text.strip()
    try:
        if chat_input.startswith("-100"):
            chat_id = int(chat_input)
        else:
            chat_id = chat_input

        chat = await app.get_chat(chat_id)
        await db.add_chat(chat.id, m.from_user.id)

        try:
            await m.bot.delete_message(m.chat.id, data.get("last_msg"))
        except:
            pass

        await m.reply(lang["chat_added"].format(chat.title))
    except Exception as e:
        await m.reply(f"Error: {e}")
    await state.clear()
