# bot_telegram_webcam.py
import logging
import os
from datetime import datetime
from pathlib import Path

import cv2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

INITIAL_MESSAGE = """👋 Ciao! Sono il bot webcam del Raspberry.

Cosa posso fare:
• 📸 Scatta foto: cattura una foto dalla webcam e la invia in chat
• 🛑 Stop: arresta il bot
"""

PHOTO_DIR = Path("./img")
PHOTO_DIR.mkdir(parents=True, exist_ok=True)


def read_token(path: str = "token.txt") -> str:
    token = Path(path).read_text(encoding="utf-8").strip()
    if not token:
        raise ValueError("Token vuoto: controlla il contenuto di token.txt")
    return token


TOKEN = read_token("token.txt")


def build_main_menu() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton("📸 Scatta foto", callback_data="take_photo")],
        [InlineKeyboardButton("🛑 Stop", callback_data="stop")]
    ]
    return InlineKeyboardMarkup(kb)


def build_back_menu() -> InlineKeyboardMarkup:
    kb = [[InlineKeyboardButton("« Menu", callback_data="menu")]]
    return InlineKeyboardMarkup(kb)


def capture_photo() -> Path:
    filename = datetime.now().strftime("foto_%Y%m%d_%H%M%S.jpg")
    filepath = PHOTO_DIR / filename

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Impossibile aprire la webcam")

    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise RuntimeError("Impossibile catturare l'immagine dalla webcam")

    ok = cv2.imwrite(str(filepath), frame)
    if not ok:
        raise RuntimeError("Impossibile salvare l'immagine su disco")

    return filepath


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        INITIAL_MESSAGE,
        reply_markup=build_main_menu()
    )


async def photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("📸 Scatto foto in corso...")
    try:
        photo_path = capture_photo()
        with open(photo_path, "rb") as photo_file:
            await update.message.reply_photo(
                photo=photo_file,
                caption=f"Foto catturata: {photo_path.name}"
            )
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"Errore durante lo scatto: {e}")


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "take_photo":
        await q.edit_message_text("📸 Scatto foto in corso...")
        try:
            photo_path = capture_photo()
            with open(photo_path, "rb") as photo_file:
                await context.bot.send_photo(
                    chat_id=q.message.chat_id,
                    photo=photo_file,
                    caption=f"Foto catturata: {photo_path.name}"
                )

            await q.edit_message_text(
                "Foto inviata correttamente.",
                reply_markup=build_back_menu()
            )
        except Exception as e:
            await q.edit_message_text(
                f"Errore durante lo scatto: {e}",
                reply_markup=build_back_menu()
            )

    elif q.data == "menu":
        await q.edit_message_text(
            INITIAL_MESSAGE,
            reply_markup=build_main_menu()
        )

    elif q.data == "stop":
        await q.edit_message_text("Arresto in corso...")
        await context.application.stop()

    else:
        await q.edit_message_text(
            "Azione non riconosciuta.",
            reply_markup=build_back_menu()
        )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("foto", photo_command))
    app.add_handler(CallbackQueryHandler(on_button))

    app.run_polling()


if __name__ == "__main__":
    main()