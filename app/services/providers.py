import asyncio
import random

class ProviderResult:
    def __init__(self, success: bool, provider_message_id: str = "", error: str = ""):
        self.success = success
        self.provider_message_id = provider_message_id
        self.error = error

class EmailProvider:
    name = "email"

    async def send(self, user_id: str, body: str, **kwargs) -> ProviderResult:
        await asyncio.sleep(0.05)  
        if random.random() < 0.2:
            raise RuntimeError("Email provider: SMTP timeout")
        return ProviderResult(success=True, provider_message_id=f"email-mock-{random.randint(100000, 999999)}")

class SMSProvider:
    name = "sms"

    async def send(self, user_id: str, body: str, **kwargs) -> ProviderResult:
        await asyncio.sleep(0.03)
        if random.random() < 0.2:
            raise RuntimeError("SMS provider: carrier rejected message")
        return ProviderResult(success=True, provider_message_id=f"sms-mock-{random.randint(100000, 999999)}")

class PushProvider:
    name = "push"

    async def send(self, user_id: str, body: str, **kwargs) -> ProviderResult:
        await asyncio.sleep(0.02)
        if random.random() < 0.2:
            raise RuntimeError("Push provider: device token expired")
        return ProviderResult(success=True, provider_message_id=f"push-mock-{random.randint(100000, 999999)}")

_providers = {
    "email": EmailProvider(),
    "sms": SMSProvider(),
    "push": PushProvider(),
}

def get_provider(channel: str):
    if channel not in _providers:
        raise ValueError(f"No provider for channel: {channel}")
    return _providers[channel]
