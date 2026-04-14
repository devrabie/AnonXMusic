# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import io
import os
import re
import sys
import uuid
import traceback
from html import escape
from typing import Any, Optional, Tuple

from aiogram import types, F
from aiogram.filters import Command, Filter

from anony import anon, app, dp, config, db, userbot
from anony.helpers import format_exception, meval

class SudoFilter(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in app.sudoers

@dp.message(Command("eval", "exec"), SudoFilter())
@dp.edited_message(Command("eval", "exec"), SudoFilter())
async def eval_handler(message: types.Message, lang: dict):
    command = message.text.split(maxsplit=1)
    if len(command) < 2:
        return await message.reply(lang["eval_inp"])

    code = command[1]
    out_buf = io.StringIO()

    async def _eval_code() -> Tuple[str, Optional[str]]:
        async def send(*args: Any, **kwargs: Any) -> types.Message:
            return await message.reply(*args, **kwargs)

        def _print(*args: Any, **kwargs: Any) -> None:
            kwargs.setdefault("file", out_buf)
            print(*args, **kwargs)

        eval_vars = {
            "m": message,
            "r": message.reply_to_message,
            "chat": message.chat,
            "user": message.from_user,
            "app": app,
            "anon": anon,
            "db": db,
            "client": app,
            "ub": userbot,
            "ikb": types.InlineKeyboardButton,
            "ikm": types.InlineKeyboardMarkup,
            "send": send,
            "config": config,
            "print": _print,
            "os": os,
            "re": re,
            "sys": sys,
            "tb": traceback,
        }

        try:
            result = await meval(code, globals(), **eval_vars)
            return "", result
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            snippet_tb = next(
                (i for i, f in enumerate(tb) if f.filename == "<string>"), -1
            )
            formatted_tb = format_exception(
                e, tb[snippet_tb:] if snippet_tb != -1 else tb
            )
            return lang["eval_error"], formatted_tb

    _, result = await _eval_code()

    if result is not None or not out_buf.getvalue():
        print(result, file=out_buf)

    output = out_buf.getvalue().strip()
    response = lang["eval_out"].format(escape(output))

    if len(response) > 4096:
        from aiogram.types import BufferedInputFile
        return await message.reply_document(
            document=BufferedInputFile(output.encode(), filename=f"{uuid.uuid4().hex[:8].lower()}.txt"),
            disable_notification=True
        )

    await message.reply(response)
