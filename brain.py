import json
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

SYSTEM_PROMPT = """
Ты аналитик лидов по банкротству. 
Твоя задача: оценить сообщение пользователя (0 - мусор/реклама, 1 - вопрос, 2 - горячий клиент с проблемой).
Вытащить город и краткую суть.
Верни ТОЛЬКО JSON: {"score": int, "city": "str/null", "summary": "str"}
"""

async def analyze_lead(text):
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini", # Или gpt-3.5-turbo для экономии
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.0
        )
        content = response.choices[0].message.content
        # Очистка от markdown, если модель вернет ```json ... ```
        clean_json = content.replace("```json", "").replace("```", "")
        return json.loads(clean_json)
    except Exception as e:
        print(f"AI Error: {e}")
        return {"score": 0, "city": None, "summary": "Error"}
