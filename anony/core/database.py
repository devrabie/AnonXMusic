# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import aiosqlite
from random import randint
from time import time
from anony import config, logger, userbot

class Database:
    def __init__(self):
        self.db_path = "anony.db"
        self.conn = None

        self.admin_list = {}
        self.active_calls = {}
        self.admin_play = []
        self.blacklisted = []
        self.cmd_delete = []
        self.loop = {}
        self.notified = []
        self.logger = False

        self.assistant = {}
        self.auth = {}
        self.chats = []
        self.lang = {}
        self.users = []

    async def connect(self) -> None:
        try:
            start = time()
            self.conn = await aiosqlite.connect(self.db_path)
            await self.conn.execute("PRAGMA journal_mode=WAL;")
            await self.conn.execute("PRAGMA busy_timeout=5000;")
            await self._create_tables()
            logger.info(f"Database connection successful. ({time() - start:.2f}s)")
            await self.load_cache()
        except Exception as e:
            raise SystemExit(f"Database connection failed: {type(e).__name__}") from e

    async def _create_tables(self):
        await self.conn.execute("CREATE TABLE IF NOT EXISTS auth (chat_id INTEGER, user_id INTEGER, PRIMARY KEY(chat_id, user_id))")
        await self.conn.execute("CREATE TABLE IF NOT EXISTS assistant (chat_id INTEGER PRIMARY KEY, num INTEGER)")
        await self.conn.execute("CREATE TABLE IF NOT EXISTS blacklist_chats (chat_id INTEGER PRIMARY KEY)")
        await self.conn.execute("CREATE TABLE IF NOT EXISTS blacklist_users (user_id INTEGER PRIMARY KEY)")
        await self.conn.execute("CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER PRIMARY KEY, cmd_delete BOOLEAN DEFAULT 0, admin_play BOOLEAN DEFAULT 0, stream_url TEXT, stream_status BOOLEAN DEFAULT 0, added_by INTEGER)")
        await self.conn.execute("CREATE TABLE IF NOT EXISTS lang (chat_id INTEGER PRIMARY KEY, lang_code TEXT)")
        await self.conn.execute("CREATE TABLE IF NOT EXISTS logger (status BOOLEAN)")
        await self.conn.execute("CREATE TABLE IF NOT EXISTS sudoers (user_id INTEGER PRIMARY KEY)")
        await self.conn.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
        await self.conn.execute("CREATE TABLE IF NOT EXISTS sessions (name TEXT PRIMARY KEY, string TEXT)")
        await self._migrate_tables()
        await self.conn.commit()

    async def _migrate_tables(self):
        try:
            await self.conn.execute("ALTER TABLE chats ADD COLUMN stream_url TEXT")
        except Exception:
            pass
        try:
            await self.conn.execute("ALTER TABLE chats ADD COLUMN stream_status BOOLEAN DEFAULT 0")
        except Exception:
            pass
        try:
            await self.conn.execute("ALTER TABLE chats ADD COLUMN added_by INTEGER")
        except Exception:
            pass
        try:
            await self.conn.execute("ALTER TABLE chats ADD COLUMN stream_type TEXT DEFAULT 'audio'")
        except Exception:
            pass
        try:
            await self.conn.execute("ALTER TABLE chats ADD COLUMN stream_source TEXT DEFAULT 'url'")
        except Exception:
            pass

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()
        logger.info("Database connection closed.")

    # CACHE
    async def get_call(self, chat_id: int) -> bool:
        return chat_id in self.active_calls

    async def add_call(self, chat_id: int) -> None:
        self.active_calls[chat_id] = 1

    async def remove_call(self, chat_id: int) -> None:
        self.active_calls.pop(chat_id, None)

    async def playing(self, chat_id: int, paused: bool = None) -> bool | None:
        if paused is not None:
            self.active_calls[chat_id] = int(not paused)
        return bool(self.active_calls.get(chat_id, 0))

    async def get_admins(self, chat_id: int, reload: bool = False) -> list[int]:
        from anony.helpers._admins import reload_admins
        if chat_id not in self.admin_list or reload:
            self.admin_list[chat_id] = await reload_admins(chat_id)
        return self.admin_list[chat_id]

    async def get_loop(self, chat_id: int) -> int:
        return self.loop.get(chat_id, 0)

    async def set_loop(self, chat_id: int, count: int) -> None:
        self.loop[chat_id] = count

    # AUTH METHODS
    async def _get_auth(self, chat_id: int) -> set[int]:
        if chat_id not in self.auth:
            async with self.conn.execute("SELECT user_id FROM auth WHERE chat_id = ?", (chat_id,)) as cursor:
                rows = await cursor.fetchall()
                self.auth[chat_id] = {row[0] for row in rows}
        return self.auth[chat_id]

    async def is_auth(self, chat_id: int, user_id: int) -> bool:
        return user_id in await self._get_auth(chat_id)

    async def add_auth(self, chat_id: int, user_id: int) -> None:
        users = await self._get_auth(chat_id)
        if user_id not in users:
            users.add(user_id)
            await self.conn.execute("INSERT OR IGNORE INTO auth (chat_id, user_id) VALUES (?, ?)", (chat_id, user_id))
            await self.conn.commit()

    async def rm_auth(self, chat_id: int, user_id: int) -> None:
        users = await self._get_auth(chat_id)
        if user_id in users:
            users.discard(user_id)
            await self.conn.execute("DELETE FROM auth WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
            await self.conn.commit()

    # ASSISTANT METHODS
    async def set_assistant(self, chat_id: int) -> int:
        from anony import userbot
        if not userbot.clients:
            return 1
        num = randint(1, len(userbot.clients))
        await self.conn.execute("INSERT OR REPLACE INTO assistant (chat_id, num) VALUES (?, ?)", (chat_id, num))
        await self.conn.commit()
        self.assistant[chat_id] = num
        return num

    async def get_assistant(self, chat_id: int):
        from anony import anon
        if chat_id not in self.assistant:
            async with self.conn.execute("SELECT num FROM assistant WHERE chat_id = ?", (chat_id,)) as cursor:
                row = await cursor.fetchone()
                num = row[0] if row else await self.set_assistant(chat_id)
                self.assistant[chat_id] = num

        if not anon.clients:
            logger.warning(f"No streaming clients (anon.clients) available for chat {chat_id}.")
            return None

        try:
            return anon.clients[self.assistant[chat_id] - 1]
        except IndexError:
            logger.warning(f"Assistant index {self.assistant[chat_id]-1} out of range for anon.clients.")
            return None

    async def get_client(self, chat_id: int):
        from anony import userbot
        if chat_id not in self.assistant:
            await self.get_assistant(chat_id)

        num = self.assistant.get(chat_id)
        if not num or num > len(userbot.clients):
            return None

        return userbot.clients[num - 1]

    # BLACKLIST METHODS
    async def add_blacklist(self, chat_id: int) -> None:
        if str(chat_id).startswith("-"):
            if chat_id not in self.blacklisted:
                self.blacklisted.append(chat_id)
                await self.conn.execute("INSERT OR IGNORE INTO blacklist_chats (chat_id) VALUES (?)", (chat_id,))
                await self.conn.commit()
            return
        await self.conn.execute("INSERT OR IGNORE INTO blacklist_users (user_id) VALUES (?)", (chat_id,))
        await self.conn.commit()

    async def del_blacklist(self, chat_id: int) -> None:
        if str(chat_id).startswith("-"):
            if chat_id in self.blacklisted:
                self.blacklisted.remove(chat_id)
                await self.conn.execute("DELETE FROM blacklist_chats WHERE chat_id = ?", (chat_id,))
                await self.conn.commit()
            return
        await self.conn.execute("DELETE FROM blacklist_users WHERE user_id = ?", (chat_id,))
        await self.conn.commit()

    async def get_blacklisted(self, chat: bool = False) -> list[int]:
        if chat:
            if not self.blacklisted:
                async with self.conn.execute("SELECT chat_id FROM blacklist_chats") as cursor:
                    rows = await cursor.fetchall()
                    self.blacklisted.extend([row[0] for row in rows])
            return self.blacklisted
        async with self.conn.execute("SELECT user_id FROM blacklist_users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    # CHAT METHODS
    async def is_chat(self, chat_id: int) -> bool:
        return chat_id in self.chats

    async def add_chat(self, chat_id: int, user_id: int = None) -> None:
        if not await self.is_chat(chat_id):
            self.chats.append(chat_id)

        await self.conn.execute(
            "INSERT INTO chats (chat_id, added_by) VALUES (?, ?) ON CONFLICT(chat_id) DO UPDATE SET added_by = COALESCE(added_by, excluded.added_by)",
            (chat_id, user_id)
        )
        await self.conn.commit()

    async def rm_chat(self, chat_id: int) -> None:
        if await self.is_chat(chat_id):
            self.chats.remove(chat_id)
            await self.conn.execute("DELETE FROM chats WHERE chat_id = ?", (chat_id,))
            await self.conn.commit()

    async def get_chats(self, user_id: int = None) -> list:
        if user_id:
            async with self.conn.execute("SELECT chat_id FROM chats WHERE added_by = ?", (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
        if not self.chats:
            async with self.conn.execute("SELECT chat_id FROM chats") as cursor:
                rows = await cursor.fetchall()
                self.chats.extend([row[0] for row in rows])
        return self.chats

    # STREAM METHODS
    async def get_stream(self, chat_id: int):
        async with self.conn.execute("SELECT stream_url, stream_status, stream_type, stream_source FROM chats WHERE chat_id = ?", (chat_id,)) as cursor:
            row = await cursor.fetchone()
            return row if row else (None, False, "audio", "url")

    async def set_stream(self, chat_id: int, url: str = None, status: bool = None, stype: str = None, source: str = None):
        if url is not None:
            await self.conn.execute("UPDATE chats SET stream_url = ? WHERE chat_id = ?", (url, chat_id))
        if status is not None:
            await self.conn.execute("UPDATE chats SET stream_status = ? WHERE chat_id = ?", (status, chat_id))
        if stype is not None:
            await self.conn.execute("UPDATE chats SET stream_type = ? WHERE chat_id = ?", (stype, chat_id))
        if source is not None:
            await self.conn.execute("UPDATE chats SET stream_source = ? WHERE chat_id = ?", (source, chat_id))
        await self.conn.commit()

    async def get_active_streams(self) -> list:
        async with self.conn.execute("SELECT chat_id, stream_url, stream_type, stream_source FROM chats WHERE stream_status = 1") as cursor:
            rows = await cursor.fetchall()
            return rows

    # COMMAND DELETE
    async def get_cmd_delete(self, chat_id: int) -> bool:
        if chat_id not in self.cmd_delete:
            async with self.conn.execute("SELECT cmd_delete FROM chats WHERE chat_id = ?", (chat_id,)) as cursor:
                row = await cursor.fetchone()
                if row and row[0]:
                    self.cmd_delete.append(chat_id)
        return chat_id in self.cmd_delete

    async def set_cmd_delete(self, chat_id: int, delete: bool = False) -> None:
        if delete:
            if chat_id not in self.cmd_delete:
                self.cmd_delete.append(chat_id)
        else:
            if chat_id in self.cmd_delete:
                self.cmd_delete.remove(chat_id)
        await self.conn.execute("INSERT INTO chats (chat_id, cmd_delete) VALUES (?, ?) ON CONFLICT(chat_id) DO UPDATE SET cmd_delete = excluded.cmd_delete", (chat_id, delete))
        await self.conn.commit()

    # LANGUAGE METHODS
    async def set_lang(self, chat_id: int, lang_code: str):
        await self.conn.execute("INSERT INTO lang (chat_id, lang_code) VALUES (?, ?) ON CONFLICT(chat_id) DO UPDATE SET lang_code = excluded.lang_code", (chat_id, lang_code))
        await self.conn.commit()
        self.lang[chat_id] = lang_code

    async def get_lang(self, chat_id: int) -> str:
        if chat_id not in self.lang:
            async with self.conn.execute("SELECT lang_code FROM lang WHERE chat_id = ?", (chat_id,)) as cursor:
                row = await cursor.fetchone()
                self.lang[chat_id] = row[0] if row else config.LANG_CODE
        return self.lang[chat_id]

    # LOGGER METHODS
    async def is_logger(self) -> bool:
        return self.logger

    async def get_logger(self) -> bool:
        async with self.conn.execute("SELECT status FROM logger") as cursor:
            row = await cursor.fetchone()
            if row:
                self.logger = bool(row[0])
        return self.logger

    async def set_logger(self, status: bool) -> None:
        self.logger = status
        await self.conn.execute("DELETE FROM logger")
        await self.conn.execute("INSERT INTO logger (status) VALUES (?)", (status,))
        await self.conn.commit()

    # PLAY MODE METHODS
    async def get_play_mode(self, chat_id: int) -> bool:
        if chat_id not in self.admin_play:
            async with self.conn.execute("SELECT admin_play FROM chats WHERE chat_id = ?", (chat_id,)) as cursor:
                row = await cursor.fetchone()
                if row and row[0]:
                    self.admin_play.append(chat_id)
        return chat_id in self.admin_play

    async def set_play_mode(self, chat_id: int, remove: bool = False) -> None:
        admin_play = not remove
        if admin_play:
            if chat_id not in self.admin_play:
                self.admin_play.append(chat_id)
        else:
            if chat_id in self.admin_play:
                self.admin_play.remove(chat_id)
        await self.conn.execute("INSERT INTO chats (chat_id, admin_play) VALUES (?, ?) ON CONFLICT(chat_id) DO UPDATE SET admin_play = excluded.admin_play", (chat_id, admin_play))
        await self.conn.commit()

    # SUDO METHODS
    async def add_sudo(self, user_id: int) -> None:
        await self.conn.execute("INSERT OR IGNORE INTO sudoers (user_id) VALUES (?)", (user_id,))
        await self.conn.commit()

    async def del_sudo(self, user_id: int) -> None:
        await self.conn.execute("DELETE FROM sudoers WHERE user_id = ?", (user_id,))
        await self.conn.commit()

    async def get_sudoers(self) -> list[int]:
        async with self.conn.execute("SELECT user_id FROM sudoers") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    # USER METHODS
    async def is_user(self, user_id: int) -> bool:
        return user_id in self.users

    async def add_user(self, user_id: int) -> None:
        if not await self.is_user(user_id):
            self.users.append(user_id)
            await self.conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            await self.conn.commit()

    async def rm_user(self, user_id: int) -> None:
        if await self.is_user(user_id):
            self.users.remove(user_id)
            await self.conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            await self.conn.commit()

    async def get_users(self) -> list:
        if not self.users:
            async with self.conn.execute("SELECT user_id FROM users") as cursor:
                rows = await cursor.fetchall()
                self.users.extend([row[0] for row in rows])
        return self.users

    # SESSION METHODS
    async def get_session(self, name: str) -> str | None:
        async with self.conn.execute("SELECT string FROM sessions WHERE name = ?", (name,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

    async def set_session(self, name: str, string: str) -> None:
        await self.conn.execute("INSERT OR REPLACE INTO sessions (name, string) VALUES (?, ?)", (name, string))
        await self.conn.commit()

    async def load_cache(self) -> None:
        await self.get_chats()
        await self.get_users()
        await self.get_blacklisted(True)
        await self.get_logger()
        logger.info("Database cache loaded.")
