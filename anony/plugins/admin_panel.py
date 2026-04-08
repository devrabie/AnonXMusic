# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

from pyrogram import filters, types, Client
from pytgcalls import PyTgCalls
from anony import app, db, lang, userbot, config, logger, anon
from anony.helpers import buttons

@app.on_message(filters.command(["admin", "panel"]) & filters.user(app.owner) & filters.private)
@lang.language()
async def _admin_panel(_, m: types.Message):
    await m.reply_text(
        text=m.lang["admin_panel"],
        reply_markup=buttons.admin_panel_markup(m.lang)
    )

@app.on_callback_query(filters.regex("admin_panel") & filters.user(app.owner))
@lang.language()
async def _admin_panel_cb(_, query: types.CallbackQuery):
    await query.edit_message_text(
        text=query.lang["admin_panel"],
        reply_markup=buttons.admin_panel_markup(query.lang)
    )

@app.on_callback_query(filters.regex("manage_ass") & filters.user(app.owner))
@lang.language()
async def _manage_ass(_, query: types.CallbackQuery):
    await query.edit_message_text(
        text=query.lang["manage_assistants"],
        reply_markup=buttons.assistants_markup(query.lang, userbot.clients)
    )

@app.on_callback_query(filters.regex("add_ass") & filters.user(app.owner))
@lang.language()
async def _add_ass(_, query: types.CallbackQuery):
    response = await app.ask(
        query.message.chat.id,
        query.lang["enter_session"],
        reply_markup=buttons.cancel_markup(query.lang),
        timeout=60
    )
    if not response or not response.text:
        return

    session = response.text
    new_client = Client(
        name="AnonyTemp",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        session_string=session,
        in_memory=True
    )

    try:
        await new_client.start()
        me = await new_client.get_me()
        await db.set_session(f"assistant_{me.id}", session)
        await userbot.boot_client(len(userbot.clients) + 1, new_client)

        # Initialize calling client for the new assistant
        call_client = PyTgCalls(new_client, cache_duration=100)
        await call_client.start()
        anon.clients.append(call_client)
        await anon.decorators(call_client)

        await response.reply_text(query.lang["assistant_added"])
    except Exception as e:
        await response.reply_text(f"{query.lang['invalid_session']}\n\nError: {e}")
    finally:
        # We don't stop it if it was successfully added to userbot.clients and it's handled there
        # But boot_client already adds it. Wait, userbot.boot_client calls ub.start() again?
        # No, boot_client takes the started client.
        pass

@app.on_callback_query(filters.regex(r"del_ass (\d+)") & filters.user(app.owner))
@lang.language()
async def _del_ass(_, query: types.CallbackQuery):
    user_id = int(query.data.split()[1])
    await db.conn.execute("DELETE FROM sessions WHERE string LIKE ?", (f"%{user_id}%",))
    await db.conn.commit()

    # Remove from active clients
    for client in userbot.clients:
        if client.me.id == user_id:
            try:
                await client.stop()
            except:
                pass
            userbot.clients.remove(client)
            break

    # Remove from calling clients
    for call_client in anon.clients:
        if call_client.app.me.id == user_id:
            try:
                await call_client.stop()
            except:
                pass
            anon.clients.remove(call_client)
            break

    await query.answer(query.lang["assistant_deleted"])
    await _manage_ass(_, query)
