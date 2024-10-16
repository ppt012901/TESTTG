import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from bs4 import BeautifulSoup
import requests

API_TOKEN = '7854032328:AAH_5k4IDw0SmsR8aot1ZGNh6iSKJKFl0xM'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Список категорий и подкатегорий
categories = {
    "Одежда, обувь и аксессуары": [
        "Женская одежда", "Женская обувь", 
        "Мужская одежда", "Мужская обувь", 
        "Сумки, рюкзаки и чемоданы", "Аксессуары"
    ],
    "Детская одежда и обувь": [
        "Для девочек", "Для мальчиков"
    ],
    "Красота и здоровье": [
        "Приборы и аксессуары", "Парфюмерия", 
        "Средства гигиены", "Косметика", 
        "Средства для волос"
    ],
    "Часы и украшения": [
        "Ювелирные изделия", "Часы", "Бижутерия"
    ]
}

# Создаем клавиатуру с категориями
main_category_markup = ReplyKeyboardMarkup(resize_keyboard=True)
for category in categories:
    main_category_markup.add(KeyboardButton(category))

# Загружаем cookies
def load_cookies():
    with open('cookies.json', 'r') as f:
        return {cookie['name']: cookie['value'] for cookie in json.load(f)}

# Парсинг объявлений
def parse_avito(city, sub_category, amount):
    cookies = load_cookies()
    url = f"https://www.avito.ru/{city}?q={sub_category}&p=1"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'
    }

    response = requests.get(url, headers=headers, cookies=cookies)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        ads = soup.find_all('div', {'data-marker': 'item'})[:amount]

        results = []
        for ad in ads:
            title = ad.find('h3').get_text(strip=True)
            price = ad.find('span', {'data-marker': 'item-price'}).get_text(strip=True)
            link = "https://www.avito.ru" + ad.find('a')['href']
            results.append({'title': title, 'price': price, 'link': link})

        return results
    else:
        return []

# Хендлер для команды /start
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Выберите категорию:", reply_markup=main_category_markup)

# Хендлер для выбора категории
@dp.message(lambda message: message.text in categories)
async def main_category_handler(message: types.Message):
    selected_category = message.text

    # Создаем клавиатуру с подкатегориями
    sub_category_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for sub_category in categories[selected_category]:
        sub_category_markup.add(KeyboardButton(sub_category))

    await message.answer(f"Вы выбрали: {selected_category}\nТеперь выберите подкатегорию:", reply_markup=sub_category_markup)

# Хендлер для выбора подкатегории
@dp.message(lambda message: any(message.text in sub for sub in categories.values()))
async def sub_category_handler(message: types.Message):
    sub_category = message.text
    await message.answer(f"Вы выбрали подкатегорию: {sub_category}. Укажите город:")

# Хендлер для ввода города и вывода результатов
@dp.message(lambda message: message.text)
async def city_handler(message: types.Message):
    city = message.text.lower()
    await message.answer("Сколько объявлений нужно спарсить?")
    amount = int((await bot.wait_for_message()).text)

    results = parse_avito(city, message.text, amount)

    if results:
        for item in results:
            await message.answer(f"{item['title']} - {item['price']} руб.\n{item['link']}")
    else:
        await message.answer("Объявлений по указанным параметрам не найдено.")

# Запуск бота
async def main():
    dp.include_router(dp)  # Подключаем хендлеры
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
