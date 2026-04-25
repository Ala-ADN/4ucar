"""Notification dispatcher — in-app (Redis pub/sub), email (SMTP), SMS (Twilio)."""


async def dispatch(alert) -> None:
    raise NotImplementedError
