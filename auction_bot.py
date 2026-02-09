import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, update
from dotenv import load_dotenv
from database import init_db, async_session, Lead, Partner

load_dotenv()
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

# --- Admin/Partner Utils ---
async def get_or_create_partner(tg_id):
    async with async_session() as session:
        res = await session.execute(select(Partner).where(Partner.telegram_id == tg_id))
        partner = res.scalar()
        if not partner:
            partner = Partner(telegram_id=tg_id, balance=0.0)
            session.add(partner)
            await session.commit()
        return partner

# --- Handlers ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await get_or_create_partner(message.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Мой баланс", callback_data="balance")],
        [InlineKeyboardButton(text="🔥 Доступные лиды", callback_data="leads")]
    ])
    await message.answer("Привет! Это биржа лидов по Банкротству.", reply_markup=kb)

@dp.callback_query(F.data == "leads")
async def show_leads(callback: types.CallbackQuery):
    async with async_session() as session:
        # Берем последние 5 непроданных горячих лидов
        query = select(Lead).where(Lead.status == 'new', Lead.score == 2).limit(5)
        leads = (await session.execute(query)).scalars().all()
        
        if not leads:
            await callback.message.answer("Пока свежих лидов нет. Ждем парсер.")
            return

        for lead in leads:
            text = (
                f"🔥 **Новый клиент**\n"
                f"🏙 Город: {lead.city or 'Не указан'}\n"
                f"📝 Проблема: {lead.summary}\n"
                f"📅 Дата: {lead.created_at.strftime('%H:%M')}\n\n"
                f"💰 Цена контакта: 350 руб."
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Купить контакт", callback_data=f"buy_{lead.id}")]
            ])
            await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)

@dp.callback_query(F.data.startswith("buy_"))
async def buy_lead(callback: types.CallbackQuery):
    lead_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    PRICE = 350.0

    async with async_session() as session:
        # Проверка баланса
        partner_res = await session.execute(select(Partner).where(Partner.telegram_id == user_id))
        partner = partner_res.scalar()
        
        if partner.balance < PRICE:
            await callback.answer("❌ Недостаточно средств! Пополните баланс.", show_alert=True)
            return

        # Покупка (Транзакция)
        lead_res = await session.execute(select(Lead).where(Lead.id == lead_id))
        lead = lead_res.scalar()
        
        if lead.status == 'sold':
            await callback.answer("❌ Уже куплено другим!", show_alert=True)
            return

        # Списание и обновление
        partner.balance -= PRICE
        lead.status = 'sold'
        await session.commit()

        await callback.message.edit_text(
            f"✅ **Куплено!**\n\n"
            f"👤 Ссылка: {lead.source_link}\n"
            f"⚠️ Напишите клиенту аккуратно, сославшись на его вопрос.",
            parse_mode="Markdown"
        )

async def main():
    await init_db()
    print("🤖 Bot started...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
