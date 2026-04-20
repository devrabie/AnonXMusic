# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import asyncio
import collections
import html
from aiogram import types, F, enums
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from anony import app, dp, db, lang, anon, tg, queue, config
from anony.helpers import buttons, join_assistant, utils

class ManageChat(StatesGroup):
    entering_url = State()
    entering_chat_id = State()
    entering_tg_link = State()
    entering_new_name = State()

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
    await _manage_chat(query, lang)

@dp.callback_query(F.data.regexp(r"toggle_source (-?\d+)"))
async def _toggle_source(query: types.CallbackQuery, lang: dict):
    chat_id = int(query.data.split()[1])
    url, status, stype, source = await db.get_stream(chat_id)

    new_source = "playlist" if source == "url" else "url"
    await db.set_stream(chat_id, source=new_source)
    await _manage_chat(query, lang)

@dp.callback_query(F.data.regexp(r"toggle_stream (-?\d+)"))
async def _toggle_stream(query: types.CallbackQuery, lang: dict):
    chat_id = int(query.data.split()[1])
    url, status, stype, source = await db.get_stream(chat_id)

    new_status = not status
    await db.set_stream(chat_id, status=new_status)

    if new_status:
        if source == "url":
            if not url:
                return await query.answer(lang["error_no_url"], show_alert=True)
            try:
                await anon.play_media(chat_id, None, stream_url=url, video=(stype == "video"))
            except Exception as e:
                return await query.answer(f"Error: {e}", show_alert=True)
        else:
            try:
                await anon.play_next(chat_id)
            except Exception as e:
                return await query.answer(f"Error: {e}", show_alert=True)
    else:
        try:
            await anon.stop(chat_id)
        except Exception:
            pass

    await _manage_chat(query, lang)

@dp.callback_query(F.data.regexp(r"manage_playlist (-?\d+)"))
async def _manage_playlist(query: types.CallbackQuery, lang: dict):
    chat_id = int(query.data.split()[1])
    queue_list = queue.get_queue(chat_id)
    await query.message.edit_text(
        text=lang["playlist_management"],
        reply_markup=buttons.playlist_markup(lang, chat_id, queue_list)
    )

@dp.callback_query(F.data.regexp(r"clear_queue (-?\d+)"))
async def _clear_queue(query: types.CallbackQuery, lang: dict):
    chat_id = int(query.data.split()[1])
    queue.clear(chat_id)
    await query.answer(lang["queue_cleared"])
    await _manage_playlist(query, lang)

@dp.callback_query(F.data.regexp(r"del_item (-?\d+) (\d+)"))
async def _del_item(query: types.CallbackQuery, lang: dict):
    chat_id = int(query.data.split()[1])
    idx = int(query.data.split()[2])
    q = queue.queues[chat_id]
    if 0 <= idx < len(q):
        # Deque doesn't support direct index deletion easily if not using list, but we can do:
        lst = list(q)
        lst.pop(idx)
        queue.queues[chat_id] = collections.deque(lst)

    await query.answer(lang["item_deleted"])
    await _manage_playlist(query, lang)

@dp.callback_query(F.data.regexp(r"play_item (-?\d+) (\d+)"))
async def _play_item(query: types.CallbackQuery, lang: dict):
    chat_id = int(query.data.split()[1])
    idx = int(query.data.split()[2])
    q = queue.queues[chat_id]
    if 0 <= idx < len(q):
        lst = list(q)
        item = lst.pop(idx)
        # Move to front
        q.clear()
        q.append(item)
        q.extend(lst)

        await anon.stop(chat_id)
        if not await join_assistant(chat_id, lang, query.message):
            return
        await anon.play_media(chat_id, None, item)
        await query.answer(lang["playing_item"])

    await _manage_playlist(query, lang)

@dp.callback_query(F.data.regexp(r"rename_item (-?\d+) (\d+)"))
async def _rename_item_prompt(query: types.CallbackQuery, state: FSMContext, lang: dict):
    chat_id = int(query.data.split()[1])
    idx = int(query.data.split()[2])
    await state.update_data(chat_id=chat_id, idx=idx, last_msg=query.message.message_id)
    await state.set_state(ManageChat.entering_new_name)
    await query.message.edit_text(
        lang["enter_new_name"],
        reply_markup=buttons.cancel_markup(lang, f"manage_playlist {chat_id}")
    )
    await query.answer()

@dp.message(ManageChat.entering_new_name)
async def _process_new_name(m: types.Message, state: FSMContext, lang: dict):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    idx = data.get("idx")
    new_name = m.text.strip()

    q = queue.queues[chat_id]
    if 0 <= idx < len(q):
        q[idx].title = new_name
        await m.reply(lang["name_updated"])

    try:
        await m.bot.delete_message(m.chat.id, data.get("last_msg"))
    except:
        pass

    await state.clear()
    # Return to playlist
    from aiogram.types import CallbackQuery
    mock_query = CallbackQuery(
        id="0",
        from_user=m.from_user,
        chat_instance="0",
        message=m,
        data=f"manage_playlist {chat_id}"
    )
    await _manage_playlist(mock_query, lang)

@dp.callback_query(F.data.regexp(r"set_url (-?\d+)"))
async def _set_url_prompt(query: types.CallbackQuery, state: FSMContext, lang: dict):
    chat_id = int(query.data.split()[1])
    await state.update_data(chat_id=chat_id, last_msg=query.message.message_id)
    await state.set_state(ManageChat.entering_url)
    await query.message.edit_text(
        lang["enter_url"],
        reply_markup=buttons.cancel_markup(lang, f"manage_chat {chat_id}")
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

@dp.callback_query(F.data.regexp(r"play_target (-?\d+) (.+)"))
async def _play_target_cb(query: types.CallbackQuery, lang: dict):
    chat_id = int(query.data.split()[1])
    command = query.data.split(maxsplit=2)[2]

    # Mock a message for process_play
    mock_msg = query.message
    mock_msg.text = command
    mock_msg.from_user = query.from_user

    video = "vplay" in command
    force = "force" in command

    await process_play(mock_msg, lang, chat_id, command, video, force)

@dp.callback_query(F.data == "add_chat_manual")
async def _add_chat_manual_prompt(query: types.CallbackQuery, state: FSMContext, lang: dict):
    await state.update_data(last_msg=query.message.message_id)
    await state.set_state(ManageChat.entering_chat_id)
    await query.message.edit_text(
        lang["enter_chat_id"],
        reply_markup=buttons.cancel_markup(lang, "manage_chats")
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

@dp.callback_query(F.data.regexp(r"add_local (-?\d+)"))
async def _add_local_prompt(query: types.CallbackQuery, state: FSMContext, lang: dict):
    chat_id = int(query.data.split()[1])
    await state.update_data(chat_id=chat_id, last_msg=query.message.message_id)
    await state.set_state(ManageChat.entering_tg_link)
    await query.message.edit_text(
        lang["enter_telegram_link"],
        reply_markup=buttons.cancel_markup(lang, f"manage_playlist {chat_id}")
    )
    await query.answer()

@dp.message(ManageChat.entering_tg_link)
async def _process_tg_link(m: types.Message, state: FSMContext, lang: dict):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    link = m.text.strip()

    try:
        sent = await m.reply(lang["play_searching"])
        media = await tg.get_from_link(link, sent, lang)
        if not media:
             return await sent.edit_text(lang["play_not_found"].format(config.SUPPORT_CHAT))

        # Associate with the user who added it
        media.user = m.from_user.mention_html()
        position = queue.add(chat_id, media)
        if position == -2:
             await sent.delete()
             return await m.reply(lang["play_duplicate"])

        await m.reply(
            lang["play_queued"].format(
                position,
                media.url or "#",
                html.escape(media.title),
                media.duration,
                m.from_user.mention_html(),
            ),
            disable_web_page_preview=True
        )
        await sent.delete()

        try:
            await m.bot.delete_message(m.chat.id, data.get("last_msg"))
        except:
            pass

    except Exception as e:
        await m.reply(f"Error: {e}")

    await state.clear()
