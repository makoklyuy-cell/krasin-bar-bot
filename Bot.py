import os
import calendar
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from PIL import Image, ImageDraw

TOKEN = os.getenv("BOT_TOKEN")

users = {
    "makoklyuy": "Гоша",
    "sokolovpeter": "Петя",
    "RNFRI": "Артём"
}

bartenders = ["Гоша","Петя"]
reserve = "Артём"

keyboard = [
["📅 Сегодня","👤 Мои смены"],
["🗓 Месяц","📷 Календарь"],
["🔄 Обновить месяц","❌ Не могу выйти"]
]

reply_markup = ReplyKeyboardMarkup(keyboard,resize_keyboard=True)

schedule = {}

def generate_schedule():

    global schedule

    today = datetime.now()
    year = today.year
    month = today.month

    cal = calendar.monthcalendar(year,month)

    new_schedule = {}
    index = 0

    for week in cal:
        for day in week:

            if day == 0:
                continue

            date = f"{day:02d}.{month:02d}"

            weekday = datetime(year,month,day).weekday()

            main = bartenders[index%2]
            second = bartenders[(index+1)%2]

            shifts = []

            if weekday in [6,0,1,2]:
                shifts.append(f"15:00 {main}")

            elif weekday == 3:
                shifts.append(f"17:00 {main}")

            elif weekday in [4,5]:
                shifts.append(f"17:00 {main}")
                shifts.append(f"20:00 {second}")

            new_schedule[date] = shifts
            index += 1

    schedule = new_schedule

generate_schedule()

def auto_generate():

    today = datetime.now()

    if today.day == 25:
        generate_schedule()

scheduler = BackgroundScheduler()
scheduler.add_job(auto_generate,"interval",hours=12)
scheduler.start()

def create_calendar():

    img = Image.new("RGB",(900,1200),"white")
    draw = ImageDraw.Draw(img)

    draw.text((40,20),"Krasin Bar график смен",fill="black")

    y = 80

    for date in schedule:

        shifts = ", ".join(schedule[date])
        text = f"{date}   {shifts}"

        draw.text((40,y),text,fill="black")

        y += 30

    file = "calendar.jpg"
    img.save(file)

    return file

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    username = update.message.from_user.username

    if username not in users:

        await update.message.reply_text("Нет доступа.")
        return

    await update.message.reply_text(
        "🍸 KrasinBar расписание",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    username = update.message.from_user.username

    if username not in users:
        return

    worker = users[username]

    if text == "📅 Сегодня":

        today = datetime.now().strftime("%d.%m")

        if today in schedule:

            shifts = "\n".join(schedule[today])

            await update.message.reply_text(
                f"🍸 Сегодня\n\n{shifts}"
            )

        else:

            await update.message.reply_text("Сегодня смен нет")

    elif text == "🗓 Месяц":

        msg = "🍸 Расписание\n\n"

        for date in schedule:

            shifts = ", ".join(schedule[date])

            msg += f"{date} — {shifts}\n"

        await update.message.reply_text(msg)

    elif text == "👤 Мои смены":

        msg = "🍸 Твои смены\n\n"

        for date in schedule:

            for shift in schedule[date]:

                if worker in shift:
                    msg += f"{date} {shift}\n"

        await update.message.reply_text(msg)

    elif text == "📷 Календарь":

        file = create_calendar()

        await update.message.reply_photo(
            photo=open(file,"rb")
        )

    elif text == "🔄 Обновить месяц":

        generate_schedule()

        await update.message.reply_text(
            "✅ Новый график создан"
        )

    elif text == "❌ Не могу выйти":

        today = datetime.now().strftime("%d.%m")

        if today not in schedule:

            await update.message.reply_text("Сегодня нет смен.")
            return

        shifts = schedule[today]

        for shift in shifts:

            if worker in shift:

                other = [b for b in bartenders if b != worker][0]

                await update.message.reply_text(
                    f"⚠️ {worker} не может выйти.\n\nПредлагаем смену: {other}\nЕсли он не сможет — выйдет {reserve}"
                )

                return

        await update.message.reply_text(
            "Сегодня у тебя нет смены."
        )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(MessageHandler(filters.TEXT,handle_message))

app.run_polling()
