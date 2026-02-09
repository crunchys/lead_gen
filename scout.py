import asyncio
import os
from telethon import TelegramClient, functions
from sqlalchemy import select
from dotenv import load_dotenv
from database import init_db, async_session, Source

load_dotenv()

api_id = int(os.getenv('TG_API_ID'))
api_hash = os.getenv('TG_API_HASH')
keywords = os.getenv('NICHE_KEYWORDS').split(',')

client = TelegramClient('scout_session', api_id, api_hash)

async def search_and_save():
    await client.start()
    print("🕵️ Scout started scanning...")
    
    async with async_session() as session:
        for key in keywords:
            key = key.strip()
            print(f"🔎 Searching for: {key}")
            try:
                result = await client(functions.contacts.SearchRequest(q=key, limit=20))
                for chat in result.chats:
                    if hasattr(chat, 'username') and chat.username:
                        link = f"https://t.me/{chat.username}"
                        
                        # Проверка на дубли через SQLAlchemy
                        existing = await session.execute(
                            select(Source).where(Source.link == link)
                        )
                        if not existing.scalar():
                            new_source = Source(platform='telegram', link=link, title=chat.title)
                            session.add(new_source)
                            print(f"   ✅ Added: {chat.title} ({link})")
                        else:
                            print(f"   ⏭️ Already exists: {chat.title}")
            except Exception as e:
                print(f"Error searching '{key}': {e}")
            
            await asyncio.sleep(2)  # Anti-spam delay
        
        await session.commit()
    print("🏁 Scouting finished.")

async def main():
    await init_db()
    await search_and_save()

if __name__ == '__main__':
    asyncio.run(main())
