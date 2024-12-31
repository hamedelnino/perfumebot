import json
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.constants import ParseMode  # وارد کردن ParseMode از telegram.constants

# توکن ربات تلگرام
TOKEN = "7742797375:AAEb1gpZJpHp0Lc-lZGIsodqV4pR88GpAhE"

# شناسه تلگرام مالک
OWNER_ID = "132515930"

with open("perfumes.json", "r", encoding="utf-8") as file:
    perfumes = json.load(file)

SELECTING_PERFUME, ENTERING_VOLUME, WAITING_RECEIPT = range(3)

user_info = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = "سلام! به ربات عطر فروشی خوش آمدید. لطفاً عطر مورد نظر خود را انتخاب کنید:\n\n"
    keyboard = []

    # ایجاد دکمه برای هر عطر
    for perfume in perfumes:
        response += f"{perfume['name']} - قیمت: {perfume['price']} تومان\n"
        keyboard.append([KeyboardButton(f"{perfume['name']}")])

    # افزودن دکمه "تمام" جداگانه
    keyboard.append([KeyboardButton("تمام")])  

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)

    await update.message.reply_text(response, reply_markup=reply_markup)
    return SELECTING_PERFUME

async def select_perfume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    selected_perfume_name = update.message.text
    selected_perfume = next((perfume for perfume in perfumes if perfume['name'] == selected_perfume_name), None)

    if selected_perfume:
        user_id = update.message.from_user.id
        if user_id not in user_info:
            user_info[user_id] = {"selected_perfumes": []}

        user_info[user_id]["selected_perfumes"].append({"perfume": selected_perfume, "volume": None, "price": None})

        await update.message.reply_text(
            f"شما عطر {selected_perfume['name']} را انتخاب کرده‌اید. لطفاً حجم عطر مورد نظر را وارد کنید (بین 2 تا 100 میلی‌لیتر)."
        )
        return ENTERING_VOLUME
    elif selected_perfume_name == "تمام":
        user_id = update.message.from_user.id
        if user_id in user_info and user_info[user_id]["selected_perfumes"]:
            total_price = 0
            details = "شما عطرهای زیر را انتخاب کرده‌اید:\n\n"

            for perfume_data in user_info[user_id]["selected_perfumes"]:
                perfume_name = perfume_data["perfume"]['name']
                volume = perfume_data["volume"]
                price = perfume_data["price"]
                total_price += price
                details += f"{perfume_name} - حجم: {volume} میلی‌لیتر - قیمت: {price} تومان\n"

            details += f"\nقیمت نهایی تمام عطرها: {total_price} تومان (بدون شیشه).\n\n"
            details += "برای پرداخت لطفاً از طریق شماره کارت زیر اقدام کنید:\n"
            details += "بانک سامان : \n<code>6219861915678410</code>\n\n"  # استفاده از <code> برای متنی که باید قابل کپی باشد
            details += "به نام محدثه آرین منش\n."
            details += "بعد از پرداخت، رسید خود را ارسال کنید."

            await update.message.reply_text(details, parse_mode=ParseMode.HTML)  # استفاده از HTML
        else:
            await update.message.reply_text("هیچ عطری انتخاب نکرده‌اید.")
        
        return WAITING_RECEIPT
    else:
        await update.message.reply_text("لطفاً یک عطر معتبر از لیست انتخاب کنید.")
        return SELECTING_PERFUME

async def set_volume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        volume = int(update.message.text)
        if 2 <= volume <= 100:
            user_id = update.message.from_user.id
            selected_perfume = user_info[user_id]["selected_perfumes"][-1]

            price = selected_perfume["perfume"]['price'] * volume
            selected_perfume["volume"] = volume
            selected_perfume["price"] = price

            await update.message.reply_text(
                f"قیمت نهایی برای {volume} میلی‌لیتر از عطر {selected_perfume['perfume']['name']}:\n"
                f"{price} تومان.\n\nبرای انتخاب عطر جدید یا اتمام خرید دستور مربوطه را وارد کنید."
            )
            return SELECTING_PERFUME
        else:
            await update.message.reply_text("حجم وارد شده باید بین 2 تا 100 میلی‌لیتر باشد.")
            return ENTERING_VOLUME
    except ValueError:
        await update.message.reply_text("لطفاً حجم را به صورت عدد وارد کنید.")
        return ENTERING_VOLUME

async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
        file_id = file.file_id
        user_id = update.message.from_user.id

        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"رسید جدید دریافت شد از کاربر {user_id}.\nبرای تأیید، دستور زیر را ارسال کنید:\n"
                 f"/confirm {user_id}"
        )
        await context.bot.send_photo(chat_id=OWNER_ID, photo=file_id)
        await update.message.reply_text("رسید شما ارسال شد. منتظر تأیید باشید.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("لطفاً تصویر رسید خود را ارسال کنید.")
        return WAITING_RECEIPT

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        command, user_id = update.message.text.split()
        user_id = int(user_id)

        if command == "/confirm" and user_id in user_info:
            await context.bot.send_message(
                chat_id=user_id,
                text="پرداخت شما تأیید شد! ممنون از خرید شما."
            )
            await update.message.reply_text("پرداخت برای کاربر تأیید شد.")
        else:
            await update.message.reply_text("شناسه کاربری نامعتبر است.")
    except ValueError:
        await update.message.reply_text("دستور تأیید نادرست است.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("فرآیند لغو شد. هر وقت خواستید می‌توانید از دستور /start استفاده کنید.")
    return ConversationHandler.END

application = Application.builder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        SELECTING_PERFUME: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_perfume)],
        ENTERING_VOLUME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_volume)],
        WAITING_RECEIPT: [MessageHandler(filters.PHOTO, receive_receipt)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

application.add_handler(conv_handler)
application.add_handler(CommandHandler("confirm", confirm_payment))

if __name__ == "__main__":
    application.run_polling()
