import os
import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Получаем токен
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    logging.error("❌ BOT_TOKEN не установлен!")
    exit(1)

# Функция для получения погоды с Яндекс.Погоды
def get_voronezh_weather():
    """Парсим погоду в Воронеже с Яндекс.Погоды"""
    try:
        url = "https://yandex.ru/pogoda/voronezh"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Получаем текущую температуру
        temp_elem = soup.find('span', {'class': 'temp__value'})
        current_temp = temp_elem.text if temp_elem else "Н/Д"
        
        # Получаем описание погоды
        condition_elem = soup.find('div', {'class': 'link__condition'})
        condition = condition_elem.text if condition_elem else "Н/Д"
        
        # Получаем ощущаемую температуру
        feels_elem = soup.find('dd', {'class': 'term__value'})
        feels_like = feels_elem.text if feels_elem else "Н/Д"
        
        # Получаем данные на день (утро, день, вечер, ночь)
        day_parts = []
        day_part_elems = soup.find_all('div', {'class': 'forecast-briefly__day'})
        
        for elem in day_part_elems[:1]:  # Берем только сегодня
            time_elems = elem.find_all('span', {'class': 'forecast-briefly__time'})
            temp_elems = elem.find_all('span', {'class': 'temp__value'})
            
            for i in range(min(len(time_elems), len(temp_elems))):
                if i < 4:  # Берем утро, день, вечер, ночь
                    day_parts.append(f"{time_elems[i].text}: {temp_elems[i].text}°C")
        
        # Формируем текст погоды
        weather_text = (
            f"🌤 **Погода в Воронеже**\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y')}\n\n"
            f"**Сейчас:**\n"
            f"🌡 Температура: {current_temp}°C\n"
            f"📝 Состояние: {condition}\n"
            f"🤔 Ощущается как: {feels_like}°C\n\n"
        )
        
        if day_parts:
            weather_text += "**Прогноз на день:**\n"
            for part in day_parts[:4]:
                weather_text += f"• {part}\n"
        
        weather_text += f"\n📊 *Источник: Яндекс.Погода*"
        
        return weather_text
        
    except Exception as e:
        logging.error(f"Ошибка при получении погоды: {e}")
        return "⚠️ Не удалось получить данные о погоде. Попробуйте позже."

# Альтернативный вариант через API (если парсинг не работает)
def get_voronezh_weather_api():
    """Альтернативный способ через открытое API"""
    try:
        # Используем openweathermap (нужен API ключ) или другой сервис
        # В качестве примера - простой запрос к wttr.in
        response = requests.get("https://wttr.in/Воронеж?format=3", timeout=10)
        if response.status_code == 200:
            return f"🌤 **Погода в Воронеже**\n\n{response.text}"
        else:
            return "⚠️ Сервис погоды временно недоступен"
    except:
        return "⚠️ Не удалось получить данные о погоде"

# Команда /start с кнопками
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("✅ Да", callback_data="yes")],
        [InlineKeyboardButton("❌ Нет", callback_data="no")],
        [InlineKeyboardButton("🌤 Погода в Воронеже", callback_data="weather")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Вы хотите чтобы я рассказал что я умею?",
        reply_markup=reply_markup
    )

# Обработка нажатия кнопок
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "yes":
        await query.edit_message_text(
            text="🤖 **Что я умею:**\n\n"
                 "• Отвечать на ваши сообщения (эхо)\n"
                 "• Команда /start - начать диалог\n"
                 "• Команда /help - помощь\n"
                 "• Команда /time - текущее время\n"
                 "• Команда /info - информация о вас\n"
                 "• Команда /weather - погода в Воронеже\n\n"
                 "Я работаю на Render 24/7! 🚀",
            parse_mode="Markdown"
        )
    elif query.data == "no":
        await query.edit_message_text(
            text="Хорошо! Если передумаете - просто напишите /help или задайте вопрос!"
        )
    elif query.data == "weather":
        weather_info = get_voronezh_weather()
        await query.edit_message_text(
            text=weather_info,
            parse_mode="Markdown"
        )

# Команда /weather
async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает погоду в Воронеже"""
    await update.message.reply_chat_action(action="typing")
    
    # Получаем погоду
    weather_info = get_voronezh_weather()
    
    # Создаем клавиатуру для обновления погоды
    keyboard = [[InlineKeyboardButton("🔄 Обновить погоду", callback_data="weather")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        weather_info,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌤 Погода", callback_data="weather")],
        [InlineKeyboardButton("🕐 Время", callback_data="time_btn")],
        [InlineKeyboardButton("👤 Инфо", callback_data="info_btn")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📚 **Доступные команды:**\n\n"
        "/start - Начать диалог с кнопками\n"
        "/help - Помощь и список команд\n"
        "/time - Текущее время\n"
        "/info - Информация о вас\n"
        "/weather - Погода в Воронеже\n\n"
        "Или используйте кнопки ниже:",
        reply_markup=reply_markup
    )

# Команда /time
async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_time = datetime.now().strftime("%H:%M:%S")
    current_date = datetime.now().strftime("%d.%m.%Y")
    await update.message.reply_text(f"📅 **Дата:** {current_date}\n⏰ **Время:** {current_time}")

# Команда /info
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👤 **Информация о вас:**\n"
        f"• Имя: {user.first_name}\n"
        f"• Фамилия: {user.last_name or 'не указана'}\n"
        f"• Username: @{user.username or 'не указан'}\n"
        f"• ID: {user.id}"
    )

# Ответ на обычные сообщения
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Вы сказали: {update.message.text}")

# Расширенная обработка кнопок для других функций
async def extended_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "time_btn":
        current_time = datetime.now().strftime("%H:%M:%S")
        current_date = datetime.now().strftime("%d.%m.%Y")
        await query.edit_message_text(f"📅 **Дата:** {current_date}\n⏰ **Время:** {current_time}")
    elif query.data == "info_btn":
        user = query.from_user
        await query.edit_message_text(
            f"👤 **Информация о вас:**\n"
            f"• Имя: {user.first_name}\n"
            f"• Username: @{user.username or 'не указан'}\n"
            f"• ID: {user.id}"
        )
    elif query.data == "weather":
        weather_info = get_voronezh_weather()
        keyboard = [[InlineKeyboardButton("🔄 Обновить погоду", callback_data="weather")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            weather_info,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

def main():
    # Создаем приложение
    app = Application.builder().token(TOKEN).build()
    
    # Регистрируем команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("time", time_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("weather", weather_command))
    
    # Регистрируем обработчики кнопок
    app.add_handler(CallbackQueryHandler(button_callback, pattern="^(yes|no|weather)$"))
    app.add_handler(CallbackQueryHandler(extended_button_callback, pattern="^(time_btn|info_btn)$"))
    
    # Регистрируем обработчик текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # Запускаем бота
    logging.info("🚀 Бот запущен с функцией погоды!")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == '__main__':
    main()
