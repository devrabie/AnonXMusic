# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types, F
from anony import dp, config, app
from anony.helpers import buttons

@dp.callback_query(F.data == "start_back")
async def _start_back(query: types.CallbackQuery, lang: dict):
    private = query.message.chat.type == "private"
    _text = (
        lang["start_pm"].format(query.from_user.first_name, app.name)
        if private
        else lang["start_gp"].format(app.name)
    )
    await query.message.edit_text(
        text=_text,
        reply_markup=buttons.start_key(lang, private, query.from_user.id)
    )

@dp.callback_query(F.data == "help")
async def _help_cb(query: types.CallbackQuery, lang: dict):
    await query.message.edit_text(
        text=lang["help_menu"],
        reply_markup=buttons.help_markup(lang)
    )

@dp.callback_query(F.data.startswith("help "))
async def _help_items(query: types.CallbackQuery, lang: dict):
    cb = query.data.split()[1]
    if cb == "back":
        return await _help_cb(query, lang)

    await query.message.edit_text(
        text=lang[f"help_{cb}"],
        reply_markup=buttons.help_markup(lang, back=True)
    )

@dp.callback_query(F.data == "close")
async def _close(query: types.CallbackQuery):
    await query.message.delete()
