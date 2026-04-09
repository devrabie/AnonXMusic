# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types, F
from aiogram.filters import Command
from anony import dp, db, lang
from anony.helpers import buttons

@dp.message(Command("lang"))
@lang.language()
async def _lang(m: types.Message):
    await m.reply(
        text=m.lang["lang_choose"],
        reply_markup=buttons.lang_markup(await db.get_lang(m.chat.id))
    )

@dp.callback_query(F.data == "language")
@lang.language()
async def _lang_cb(query: types.CallbackQuery):
    await query.message.edit_text(
        text=query.lang["lang_choose"],
        reply_markup=buttons.lang_markup(await db.get_lang(query.message.chat.id))
    )

@dp.callback_query(F.data.startswith("lang_change "))
@lang.language()
async def _lang_change(query: types.CallbackQuery):
    code = query.data.split()[1]
    curr = await db.get_lang(query.message.chat.id)
    if code == curr:
        return await query.answer(query.lang["lang_same"].format(code))

    await db.set_lang(query.message.chat.id, code)
    # Refresh language in query object for the next message
    query.lang = lang.languages[code]
    await query.message.edit_text(
        text=query.lang["lang_changed"].format(lang.lang_codes[code]),
        reply_markup=buttons.start_key(query.lang, query.message.chat.type == "private", query.from_user.id)
    )
