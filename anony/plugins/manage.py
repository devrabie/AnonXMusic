# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

from pyrogram import filters, types
from anony import app, db, lang, anon, tg, queue
from anony.helpers import buttons

@app.on_message(filters.command(["manage", "dashboard"]) & filters.private)
@lang.language()
async def _dashboard(_, m: types.Message):
    chats = await db.get_chats(user_id=m.from_user.id)
    if not chats:
        return await m.reply_text(m.lang["no_chats"])

    chat_list = []
    for chat_id in chats:
        try:
            chat = await app.get_chat(chat_id)
            chat_list.append((chat_id, chat.title))
        except Exception:
            continue

    await m.reply_text(
        text=m.lang["manage_chats"],
        reply_markup=buttons.dashboard_markup(m.lang, chat_list)
    )

@app.on_callback_query(filters.regex("manage_chats"))
@lang.language()
async def _manage_chats_cb(_, query: types.CallbackQuery):
    chats = await db.get_chats(user_id=query.from_user.id)
    if not chats:
        return await query.answer(query.lang["no_chats"], show_alert=True)

    chat_list = []
    for chat_id in chats:
        try:
            chat = await app.get_chat(chat_id)
            chat_list.append((chat_id, chat.title))
        except Exception:
            continue

    await query.edit_message_text(
        text=query.lang["manage_chats"],
        reply_markup=buttons.dashboard_markup(query.lang, chat_list)
    )

@app.on_callback_query(filters.regex(r"manage_chat (-?\d+)"))
@lang.language()
async def _manage_chat(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    url, status = await db.get_stream(chat_id)

    await query.edit_message_text(
        text=query.lang["stream_settings"].format(chat_id),
        reply_markup=buttons.stream_markup(query.lang, chat_id, status)
    )

@app.on_callback_query(filters.regex(r"toggle_stream (-?\d+)"))
@lang.language()
async def _toggle_stream(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    url, status = await db.get_stream(chat_id)

    if not url:
        return await query.answer(query.lang["enter_url"], show_alert=True)

    new_status = not status
    await db.set_stream(chat_id, status=new_status)

    if new_status:
        await anon.play_media(chat_id, query.message, stream_url=url)
        await query.answer(query.lang["stream_on"])
    else:
        await anon.stop(chat_id)
        await query.answer(query.lang["stream_off"])

    await _manage_chat(_, query)

@app.on_callback_query(filters.regex(r"set_url (-?\d+)"))
@lang.language()
async def _set_url(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    await query.edit_message_text(query.lang["enter_url"])

    response = await app.listen(query.message.chat.id, filters.text, timeout=60)
    if not response:
        return

    url = response.text
    await db.set_stream(chat_id, url=url)
    await response.reply_text(query.lang["url_set"])

    # Refresh dashboard
    m = await app.send_message(query.message.chat.id, query.lang["processing"])
    query.message = m
    await _manage_chat(_, query)

@app.on_callback_query(filters.regex("add_chat_manual"))
@lang.language()
async def _add_chat_manual(_, query: types.CallbackQuery):
    await query.edit_message_text(query.lang["enter_chat_id"])

    response = await app.listen(query.message.chat.id, filters.text, timeout=60)
    if not response:
        return

    try:
        chat_id = int(response.text)
        chat = await app.get_chat(chat_id)
        await db.add_chat(chat_id, query.from_user.id)
        await response.reply_text(query.lang["chat_added"].format(chat.title))
        await _manage_chats_cb(_, query)
    except Exception:
        await response.reply_text(query.lang["invalid_chat_id"])

@app.on_callback_query(filters.regex(r"add_local (-?\d+)"))
@lang.language()
async def _add_local(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    await query.edit_message_text(query.lang["enter_telegram_link"])

    response = await app.listen(query.message.chat.id, filters.text, timeout=60)
    if not response:
        return

    link = response.text
    sent = await response.reply_text(query.lang["processing"])

    try:
        media = await tg.get_from_link(link, sent)
        if not media:
            return await sent.edit_text(query.lang["invalid_telegram_link"])

        media.user = query.from_user.mention
        position = queue.add(chat_id, media)

        if position != 0 or await db.get_call(chat_id):
            await sent.edit_text(
                query.lang["play_queued"].format(
                    position,
                    media.url,
                    media.title,
                    media.duration,
                    query.from_user.mention,
                )
            )
        else:
            await anon.play_media(chat_id, sent, media)

    except Exception as e:
        await sent.edit_text(f"Error: {e}")

    # Refresh dashboard after a delay
    await _manage_chat(_, query)
