# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types, F
from anony import dp, lang, config, app
from anony.helpers import buttons

@dp.callback_query(F.data == "start_back")
@lang.language()
async def _start_back(query: types.CallbackQuery):
    private = query.message.chat.type == "private"
    _text = (
        query.lang["start_pm"].format(query.from_user.first_name, app.name)
        if private
        else query.lang["start_gp"].format(app.name)
    )
    await query.message.edit_text(
        text=_text,
        reply_markup=buttons.start_key(query.lang, private, query.from_user.id)
    )

@dp.callback_query(F.data == "help")
@lang.language()
async def _help_cb(query: types.CallbackQuery):
    await query.message.edit_text(
        text=query.lang["help_menu"],
        reply_markup=buttons.help_markup(query.lang)
    )

@dp.callback_query(F.data.startswith("help "))
@lang.language()
async def _help_items(query: types.CallbackQuery):
    cb = query.data.split()[1]
    if cb == "back":
        return await _help_cb(query)

    await query.message.edit_text(
        text=query.lang[f"help_{cb}"],
        reply_markup=buttons.help_markup(query.lang, back=True)
    )

@dp.callback_query(F.data == "close")
async def _close(query: types.CallbackQuery):
    await query.message.delete()
