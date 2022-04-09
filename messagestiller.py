from telethon import TelegramClient, types
from telethon.utils import get_display_name, get_peer_id
from telethon.tl.functions.messages import CreateChatRequest

from .. import loader, utils


@loader.tds
class MessageStillerMod(loader.Module):
    """Пересылает сообщения"""

    strings = {"name": "MessageStiller"}

    async def client_ready(self, client: TelegramClient, db: dict):
        self.client = client
        self.db = db

    async def stillOncmd(self, message: types.Message):
        """Включить режим пересылания сообщений в реальном времени. Используй: .stillOn <@ или ID чата с которого брать сообщения> <@ или ID чата в который пересылать (по желанию)>"""
        if not (args := utils.get_args(message)):
            return await utils.answer(
                message, "<b>[MessageStiller]</b> Нет аргументов после команды.")

        if len(args) == 1:
            try:
                to_chat = await self.client.get_entity(int(args[0]) if args[0].isdigit() or args[0].startswith("-") else args[0])
            except ValueError as e:
                return await utils.answer(
                    message, f"<b>[MessageStiller]</b> Ошибка при добавлении чата. Ошибка: {e}")

            self.db.set("MessageStiller", "global", get_peer_id(to_chat.id))
            return await utils.answer(
                message, f"<b>[MessageStiller]</b> Теперь сообщения со всех ЛС будут пересылаться в \"{get_display_name(to_chat)}\"")

        elif len(args) > 2:
            return await utils.answer(
                message, "<b>[MessageStiller]</b> Аргументов должно быть 1 или 2.")

        try:
            from_chat = await self.client.get_entity(int(args[0]) if args[0].isdigit() or args[0].startswith("-") else args[0])
            to_chat = await self.client.get_entity(int(args[1]) if args[1].isdigit() or args[1].startswith("-") else args[1])
        except ValueError as e:
            return await utils.answer(
                message, f"<b>[MessageStiller]</b> Ошибка при добавлении чата. Ошибка: {e}")

        ms = self.db.get("MessageStiller", "private", {})
        ms[str(get_peer_id(from_chat))] = get_peer_id(to_chat)
        self.db.set("MessageStiller", "private", ms)

        name1, name2 = map(get_display_name, [from_chat, to_chat])
        return await utils.answer(
            message, f"<b>[MessageStiller]</b> С {name1} в {name2}.\nВключено!")

    async def stillOffcmd(self, message: types.Message):
        """Удалить чат из логирования. Используй: .stillOff <private/groups/global> <ID чата>"""
        if not (args := utils.get_args(message)):
            return await utils.answer(
                message, "<b>[MessageStiller]</b> Нет аргументов после команды.")

        if args[0] not in ["private", "groups", "global"]:
            return await utils.answer(
                message, "<b>[MessageStiller]</b> Первый аргумент должнен быть private/groups/global.")

        if len(args) == 1 and args[0] == "global":
            self.db.set("MessageStiller", "global", None)
            return await utils.answer(
                message, "<b>[MessageStiller]</b> Функция \"Все ЛС\" отключена.")

        elif len(args) != 2:
            return await utils.answer(
                message, "<b>[MessageStiller]</b> Недостаточно аргументов.")

        current_ms = self.db.get("MessageStiller", args[0], {})
        if not current_ms.get(args[1]):
            return await utils.answer(
                message, "<b>[MessageStiller]</b> Нет чата с таким ID.")

        del current_ms[args[1]]
        self.db.set("MessageStiller", args[0], current_ms)
        return await message.edit(f"<b>[MessageStiller]</b> Из базы {args[0]} был удален айди {args[1]}.")

    async def still2groupcmd(self, message: types.Message):
        """Создать группу и пересылать сообщения туда"""
        from_chat = await self.client.get_entity(message.chat_id)
        created_chat_id = (await self.client(
            CreateChatRequest(users=[1854507738], title=f"MessageStiller: {get_display_name(from_chat)}")
        )).chats[0].id

        ms_groups = self.db.get("MessageStiller", "groups", {})
        ms_groups[from_chat.id] = created_chat_id
        self.db.set("MessageStiller", "groups", ms_groups)

        await message.delete()
        return await self.client.send_message(
            created_chat_id, f"Здесь будет весь диалог с <a href=\"tg://user?id={from_chat.id}\">{get_display_name(from_chat)}</a> (<code>{from_chat.id}</code>)")

    async def stillscmd(self, message: types.Message):
        """Вывести список чатов в которых включен модуль. Используй: .stills"""
        ms_private = self.db.get("MessageStiller", "private", {})
        ms_groups = self.db.get("MessageStiller", "groups", {})
        ms_global = self.db.get("MessageStiller", "global", None)

        text_private = text_groups = text_global = ""

        if ms_private:
            for from_chat, to_chat in ms_private.items():
                from_chat = await self.client.get_entity(int(from_chat))
                to_chat = await self.client.get_entity(int(to_chat))

                name1, name2 = map(get_display_name, [from_chat, to_chat])
                text_private += f"    • <a href=\"tg://user?id={from_chat.id}\">{name1}</a> (<code>{from_chat.id}</code>) ➜ {name2} (<code>{to_chat.id}</code>)\n"

        if ms_groups:
            for from_chat, to_chat in ms_groups.items():
                from_chat = await self.client.get_entity(int(from_chat))
                to_chat = await self.client.get_entity(int(to_chat))

                name1, name2 = map(get_display_name, [from_chat, to_chat])
                text_groups += f"    • <a href=\"tg://user?id={from_chat.id}\">{name1}</a> (<code>{from_chat.id}</code>) ➜ {name2} (<code>{to_chat.id}</code>)\n"

        if ms_global:
            to_chat = await self.client.get_entity(int(ms_global))
            name = get_display_name(to_chat)
            text_global = f"    • Все ЛС ➜ {name} (<code>{to_chat.id}</code>)\n"

        self.db.set("MessageStiller", "private", ms_private)
        self.db.set("MessageStiller", "groups", ms_groups)
        self.db.set("MessageStiller", "global", ms_global)

        return await utils.answer(
            message, f"<b>[MessageStiller]</b> Состояние модуля:\n"
                     f"ЛС (<code>private</code>):\n{text_private}\n"
                     f"Группы (<code>groups</code>):\n{text_groups}\n"
                     f"Все ЛС (<code>global</code>):\n{text_global}"
        )

    async def watcher(self, message: types.Message):
        """Отслеживать пересылку сообщений в группу"""
        if not message.is_private:
            return

        ms_private = self.db.get("MessageStiller", "private", {})
        ms_groups = self.db.get("MessageStiller", "groups", {})
        ms_global = self.db.get("MessageStiller", "global", None)

        if ms_private.get(message.chat_id, None):
            await message.forward_to(ms_private[message.chat_id])

        if ms_groups.get(message.chat_id, None):
            await message.forward_to(ms_groups[message.chat_id])

        if ms_global:
            await message.forward_to(ms_global)
