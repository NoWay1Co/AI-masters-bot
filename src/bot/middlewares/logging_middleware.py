from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from ...utils.logger import logger

class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            logger.info(
                "Message received",
                user_id=event.from_user.id,
                username=event.from_user.username,
                text=event.text[:100] if event.text else None,
                message_type=event.content_type
            )
        elif isinstance(event, CallbackQuery):
            logger.info(
                "Callback query received",
                user_id=event.from_user.id,
                username=event.from_user.username,
                data=event.data
            )
        
        result = await handler(event, data)
        return result 