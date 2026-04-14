# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types, F
from aiogram.filters import Command
from anony import dp, db, lang as lang_manager
from anony.helpers import buttons

@dp.message(Command("lang"))
async def _lang(m: types.Message, lang: dict):
    await m.reply(
        text=lang["lang_choose"],
        reply_markup=buttons.lang_markup(await db.get_lang(m.chat.id))
    )

@dp.callback_query(F.data == "language")
async def _lang_cb(query: types.CallbackQuery, lang: dict):
    await query.message.edit_text(
        text=lang["lang_choose"],
        reply_markup=buttons.lang_markup(await db.get_lang(query.message.chat.id))
    )

@dp.callback_query(F.data.startswith("lang_change "))
async def _lang_change(query: types.CallbackQuery, lang: dict):
    code = query.data.split()[1]
    curr = await db.get_lang(query.message.chat.id)
    # Get current lang for answer
    lang_dict = lang_manager.languages.get(curr, lang_manager.languages["en"])

    if code == curr:
        return await query.answer(lang_dict["lang_same"].format(code))

    await db.set_lang(query.message.chat.id, code)
    new_lang = lang_manager.languages[code]
    await query.message.edit_text(
        text=new_lang["lang_changed"].format(lang_manager.lang_codes[code]),
        reply_markup=buttons.start_key(new_lang, query.message.chat.type == "private", query.from_user.id)
    )
