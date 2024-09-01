from typing import Any, Awaitable, Callable, Dict, Optional
from aiogram.utils.i18n import gettext as _
from aiogram import BaseMiddleware
from aiogram.dispatcher.flags.getter import get_flag
from aiogram.types import TelegramObject, User, CallbackQuery
from aiolimiter import AsyncLimiter
from config import settings, DEBUG


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, default_rate: int = 1.6) -> None:
        self.limiters: Dict[str, AsyncLimiter] = {}
        self.default_rate = default_rate

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        user: Optional[User] = data.get("event_from_user")
        throttling_flag = get_flag(data["handler"], 'rate_limit')
        if throttling_flag is None:
            throttling_flag = {}
        throttling_key = throttling_flag.get('key', None)
        throttling_rate = throttling_flag.get('rate', self.default_rate)

        if not throttling_key or not user:
            return await handler(event, data)

        limiter = self.limiters.setdefault(
            f"{user.id}:{throttling_key}", AsyncLimiter(1, throttling_rate)
        )
        if limiter.has_capacity():
            async with limiter:
                return await handler(event, data)
        else:
            try:
                await event.answer(_("Не флуди! Подожди секунду!"))
            except:
                pass
