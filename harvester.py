import asyncio
import os
from telethon import TelegramClient, events
from dotenv import load_dotenv
from sqlalchemy import select
from database import init_db, async_session, Source, Lead
from brain import analyze_lead

load_dotenv()

api_id = int(os.getenv('TG_API_ID'))
api_hash = os.getenv('TG_API_HASH')

client = TelegramClient('harvester_session', api_id, api_hash)

async def get_chats_to_listen():
    async with async_session() as session:
        result = await session.execute(select(Source).where(Source.is_active == True))
        sources = result.scalars().all()
        # Превращаем ссылки https://t.me/username в username
        return [s.link.split('/')[-1] for s in sources if 't.me' in s.link]

@client.on(events.NewMessage())
async def handler(event):
    # Игнорируем свои сообщения и ботов
    if event.sender_id == (await client.get_me()).id or event.message.via_bot_id:
        return

    text = event.message.message
    if not text or len(text) < 10: return

    print(f"📨 New msg in {event.chat_id}: {text[:30]}...")

    # 1. AI Анализ
    analysis = await analyze_lead(text)
    
    if analysis['score'] >= 2: # Только горячие
        print(f"🔥 HOT LEAD FOUND! Summary: {analysis['summary']}")
        
        # 2. Сохранение в БД
        async with async_session() as session:
            sender = await event.get_sender()
            username = getattr(sender, 'username', 'NoUsername')
            
            lead = Lead(
                source_link=f"t.me/{event.chat.username}/{event.id}",
                user_id=str(sender.id),
                username=username,
                raw_text=text,
                score=analysis['score'],
                city=analysis['city'],
                summary=analysis['summary']
            )
            session.add(lead)
            await session.commit()
            
            # TODO: Тут можно вызвать webhook для уведомления бота

async def main():
    await init_db()
    chats = await get_chats_to_listen()
    print(f"🎧 Listening to {len(chats)} chats...")
    
    # Подписываемся на каналы (или просто мониторим, если уже вступили)
    # В реальной версии тут нужна логика JoinChannelRequest
    
    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
