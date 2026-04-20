# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


import json
from functools import wraps
from pathlib import Path
from aiogram import types
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from anony import db, logger

lang_codes = {
    "ar": "العربية",
    "de": "Deutsch",
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "hi": "हिन्दी",
    "ja": "日本語",
    "my": "မြန်မာဘာသာ",
    "pa": "ਪੰਜਾਬੀ",
    "pt": "Português",
    "ru": "Русский",
    "tr": "Türkçe",
    "zh": "中文"
}


class Language:
    """
    Language class for managing multilingual support using JSON language files.
    """

    def __init__(self):
        self.lang_codes = lang_codes
        self.lang_dir = Path("anony/locales")
        self.languages = self.load_files()

    def load_files(self):
        languages = {}
        lang_files = {file.stem: file for file in self.lang_dir.glob("*.json")}
        for lang_code, lang_file in lang_files.items():
            with open(lang_file, "r", encoding="utf-8") as file:
                languages[lang_code] = json.load(file)
        logger.info(f"Loaded languages: {', '.join(languages.keys())}")
        return languages

    async def get_lang(self, chat_id: int) -> dict:
        lang_code = await db.get_lang(chat_id)
        return self.languages[lang_code]

    def get_languages(self) -> dict:
        files = {f.stem for f in self.lang_dir.glob("*.json")}
        return {code: self.lang_codes[code] for code in sorted(files)}

    def language(self):
        def decorator(func):
            @wraps(func)
            async def wrapper(event, *args, **kwargs):
                if isinstance(event, types.Message):
                    user = event.from_user
                    chat = event.chat
                elif isinstance(event, types.CallbackQuery):
                    user = event.from_user
                    chat = event.message.chat if event.message else None
                else:
                    return await func(event, *args, **kwargs)

                if not user or not chat:
                    return await func(event, *args, **kwargs)

                if chat.id in db.blacklisted:
                    logger.info(f"Chat {chat.id} is blacklisted, leaving...")
                    try:
                        await event.bot.leave_chat(chat.id)
                    except:
                        pass
                    return

                lang_code = await db.get_lang(chat.id)
                lang_dict = self.languages[lang_code]

                # In aiogram, we can't easily set attributes on types, so we pass it in kwargs or context
                # But for simplicity in this migration, we might try to set it if possible or pass it explicitly.
                # Actually, many plugins use event.lang.
                try:
                    setattr(event, "lang", lang_dict)
                except AttributeError:
                    # Some types might not allow setting attributes
                    pass

                try:
                    return await func(event, *args, **kwargs)
                except (TelegramForbiddenError, TelegramBadRequest):
                    return
                except Exception as e:
                    logger.error(f"Error in handler {func.__name__}: {e}")
                    raise e

            return wrapper

        return decorator
