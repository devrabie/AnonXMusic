# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types, F
from anony import dp, app


@dp.inline_query()
async def _iquery(query: types.InlineQuery, lang: dict):
    # Inline query logic in transition
    await query.answer([])
