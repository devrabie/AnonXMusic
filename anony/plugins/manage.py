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
        return await m.reply_text(
            text=m.lang["no_chats"],
            reply_markup=buttons.dashboard_markup(m.lang, [])
        )

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
        return await query.edit_message_text(
            text=query.lang["no_chats"],
            reply_markup=buttons.dashboard_markup(query.lang, [])
        )

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
    url, status, stype, source = await db.get_stream(chat_id)

    # Check if currently playing
    is_playing = await db.get_call(chat_id)

    if is_playing:
        keyboard = buttons.controls(chat_id)
    else:
        keyboard = buttons.stream_markup(query.lang, chat_id, status, stype, source)

    await query.edit_message_text(
        text=query.lang["stream_settings"].format(chat_id),
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex(r"toggle_stype (-?\d+)"))
@lang.language()
async def _toggle_stype(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    url, status, stype, source = await db.get_stream(chat_id)

    new_type = "video" if stype == "audio" else "audio"
    await db.set_stream(chat_id, stype=new_type)
    await _manage_chat(_, query)

@app.on_callback_query(filters.regex(r"toggle_source (-?\d+)"))
@lang.language()
async def _toggle_source(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    url, status, stype, source = await db.get_stream(chat_id)

    new_source = "playlist" if source == "url" else "url"
    await db.set_stream(chat_id, source=new_source)
    await _manage_chat(_, query)

@app.on_callback_query(filters.regex(r"toggle_stream (-?\d+)"))
@lang.language()
async def _toggle_stream(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    url, status, stype, source = await db.get_stream(chat_id)

    if not url:
        return await query.answer(query.lang["enter_url"], show_alert=True)

    new_status = not status
    await db.set_stream(chat_id, status=new_status)

    if new_status:
        if source == "url":
            if not url:
                return await query.answer(query.lang["enter_url"], show_alert=True)
            await anon.play_media(chat_id, None, stream_url=url, video=(stype == "video"))
        else:
            await anon.play_next(chat_id)
        await query.answer(query.lang["stream_on"])
    else:
        await anon.stop(chat_id)
        await query.answer(query.lang["stream_off"])

    await _manage_chat(_, query)

@app.on_callback_query(filters.regex(r"set_url (-?\d+)"))
@lang.language()
async def _set_url(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    response = await app.ask(
        query.message.chat.id,
        query.lang["enter_url"],
        reply_markup=buttons.cancel_markup(query.lang),
        timeout=60
    )
    if not response or not response.text:
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
    response = await app.ask(
        query.message.chat.id,
        query.lang["enter_chat_id"],
        reply_markup=buttons.cancel_markup(query.lang),
        timeout=60
    )
    if not response or not response.text:
        return

    try:
        chat_id = response.text.strip()
        if "t.me/" in chat_id or "telegram.me/" in chat_id:
            if "/c/" in chat_id:
                chat_id = int("-100" + chat_id.split("/")[-2])
            else:
                chat_id = [p for p in chat_id.split("/") if p][-1]

        if isinstance(chat_id, str) and chat_id.startswith("-100"):
            try:
                chat_id = int(chat_id)
            except ValueError:
                pass
        elif isinstance(chat_id, str) and chat_id.replace("-", "").isdigit():
            chat_id = int(chat_id) if chat_id.startswith("-") else int("-100" + chat_id)

        # Try to resolve peer to avoid PeerIdInvalid
        try:
            await app.resolve_peer(chat_id)
        except Exception:
            pass

        chat = await app.get_chat(chat_id)
        await db.add_chat(chat.id, query.from_user.id)
        await response.reply_text(query.lang["chat_added"].format(chat.title))
        await _manage_chats_cb(_, query)
    except Exception as e:
        await response.reply_text(f"{query.lang['invalid_chat_id']}\n\nError: {e}")

@app.on_callback_query(filters.regex(r"add_local (-?\d+)"))
@lang.language()
async def _add_local(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    response = await app.ask(
        query.message.chat.id,
        query.lang["enter_telegram_link"],
        reply_markup=buttons.cancel_markup(query.lang),
        timeout=60
    )
    if not response or not response.text:
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

@app.on_callback_query(filters.regex(r"play_target (-?\d+) (.*)"))
@lang.language()
async def _play_target_cb(_, query: types.CallbackQuery):
    from anony.plugins.play import play_hndlr
    from types import SimpleNamespace
    import asyncio

    data = query.data.split(maxsplit=2)
    chat_id = int(data[1])
    command = data[2]

    # Spoof message to trigger play handler in target chat
    m = SimpleNamespace(
        chat=SimpleNamespace(id=chat_id, type=types.enums.ChatType.SUPERGROUP),
        text=command,
        command=command.split(),
        from_user=query.from_user,
        reply_to_message=None,
        reply_text=lambda *args, **kwargs: app.send_message(chat_id, *args, **kwargs),
        delete=lambda *args, **kwargs: asyncio.sleep(0),
        lang=query.lang
    )

    await query.message.delete()
    await play_hndlr(_, m)
