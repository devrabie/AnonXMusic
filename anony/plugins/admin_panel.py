# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

from aiogram import types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from pyrogram import Client
from pytgcalls import PyTgCalls
from anony import app, dp, db, userbot, config, logger, anon
from anony.helpers import buttons

class AdminState(StatesGroup):
    entering_session = State()

@dp.message(Command("admin", "panel"), F.chat.type == "private")
async def _admin_panel(m: types.Message, lang: dict):
    if str(m.from_user.id) != str(app.owner):
        return
    await m.reply(
        text=lang["admin_panel"],
        reply_markup=buttons.admin_panel_markup(lang)
    )

@dp.callback_query(F.data == "admin_panel")
async def _admin_panel_cb(query: types.CallbackQuery, lang: dict):
    if str(query.from_user.id) != str(app.owner):
        return await query.answer("Unauthorized", show_alert=True)
    await query.message.edit_text(
        text=lang["admin_panel"],
        reply_markup=buttons.admin_panel_markup(lang)
    )

@dp.callback_query(F.data == "manage_ass")
async def _manage_ass(query: types.CallbackQuery, lang: dict):
    if str(query.from_user.id) != str(app.owner):
        return
    await query.message.edit_text(
        text=lang["manage_assistants"],
        reply_markup=buttons.assistants_markup(lang, userbot.clients)
    )

@dp.callback_query(F.data == "add_ass")
async def _add_ass_prompt(query: types.CallbackQuery, state: FSMContext, lang: dict):
    if str(query.from_user.id) != str(app.owner):
        return
    await state.update_data(last_msg=query.message.message_id)
    await state.set_state(AdminState.entering_session)
    await query.message.edit_text(
        lang["enter_session"],
        reply_markup=buttons.cancel_markup(lang)
    )
    await query.answer()

@dp.message(AdminState.entering_session)
async def _process_session(m: types.Message, state: FSMContext, lang: dict):
    if str(m.from_user.id) != str(app.owner):
        return

    data = await state.get_data()
    session = m.text
    new_client = Client(
        name="AnonyTemp",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        session_string=session,
        in_memory=True
    )

    try:
        await new_client.start()
        new_client.id = new_client.me.id
        await db.set_session(f"assistant_{new_client.id}", session)
        await userbot.boot_client(len(userbot.clients) + 1, new_client)

        call_client = PyTgCalls(new_client, cache_duration=100)
        await call_client.start()
        anon.clients.append(call_client)
        await anon.decorators(call_client)

        try:
            await m.bot.delete_message(m.chat.id, data.get("last_msg"))
        except:
            pass

        await m.reply(lang["assistant_added"])
    except Exception as e:
        await m.reply(f"{lang['invalid_session']}\n\nError: {e}")
    await state.clear()

@dp.callback_query(F.data.regexp(r"del_ass (\d+)"))
async def _del_ass(query: types.CallbackQuery, lang: dict):
    if str(query.from_user.id) != str(app.owner):
        return
    user_id = int(query.data.split()[1])

    await db.conn.execute("DELETE FROM sessions WHERE string LIKE ?", (f"%{user_id}%",))
    await db.conn.commit()

    for client in userbot.clients:
        if getattr(client, "id", None) == user_id:
            try:
                await client.stop()
            except:
                pass
            userbot.clients.remove(client)
            break

    for call_client in anon.clients:
        if getattr(call_client, "id", None) == user_id:
            try:
                await call_client.stop()
            except:
                pass
            anon.clients.remove(call_client)
            break

    await query.answer(lang["assistant_deleted"])
    await _manage_ass(query, lang)
