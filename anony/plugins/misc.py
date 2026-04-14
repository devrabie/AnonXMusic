# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from aiogram import types, F
from anony import dp


@dp.message(F.video_chat_started)
async def _vc_started(m: types.Message, lang: dict):
    # logic
    pass

@dp.message(F.video_chat_ended)
async def _vc_ended(m: types.Message, lang: dict):
    # logic
    pass
