import httpx


async def notify_bot(user_id, selected_voice, selected_speed, role):
    bot_url = "http://localhost:3000/send_notification"
    payload = {
        "user_id": user_id,
        "selected_voice": selected_voice,
        "selected_speed": selected_speed,
        "role": role
    }
    async with httpx.AsyncClient() as client:
        await client.post(bot_url, json=payload)
