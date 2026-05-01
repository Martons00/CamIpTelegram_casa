# bot_telegram_cam_multi.py
import logging
import os
import time
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

INITIAL_MESSAGE = """👋 Ciao! Sono il bot camere del Raspberry.

Cosa posso fare:
• 📸 Webcam locale
• 🏠 IP Cam 1
• 🚪 IP Cam 2
• 🛑 Stop
"""

PHOTO_DIR = Path("./img")
PHOTO_DIR.mkdir(parents=True, exist_ok=True)

TOKEN = Path("token.txt").read_text(encoding="utf-8").strip()

RTSP_CAM_1 = Path("ip_cam_01.txt").read_text(encoding="utf-8").strip()
RTSP_CAM_2 = Path("ip_cam_02.txt").read_text(encoding="utf-8").strip()


def build_main_menu() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton("📸 Webcam locale", callback_data="shot_local")],
        [InlineKeyboardButton("🏠 Scatta IP Cam 1", callback_data="shot_cam1")],
        [InlineKeyboardButton("🚪 Scatta IP Cam 2", callback_data="shot_cam2")],
        [InlineKeyboardButton("🛑 Stop", callback_data="stop")]
    ]
    return InlineKeyboardMarkup(kb)


def build_back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("« Menu", callback_data="menu")]
    ])


def capture_from_source(source, prefix: str, use_ffmpeg: bool = False) -> Path:
    filename = datetime.now().strftime(f"{prefix}_%Y%m%d_%H%M%S.jpg")
    filepath = PHOTO_DIR / filename

    if use_ffmpeg:
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
        cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
    else:
        cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        raise RuntimeError(f"Impossibile aprire la sorgente: {prefix}")

    frame = None
    ret = False

    for _ in range(8):
        ret, frame = cap.read()
        if ret and frame is not None:
            time.sleep(0.1)

    cap.release()

    if not ret or frame is None:
        raise RuntimeError(f"Impossibile catturare l'immagine da: {prefix}")

    ok = cv2.imwrite(str(filepath), frame)
    if not ok:
        raise RuntimeError(f"Impossibile salvare l'immagine di: {prefix}")

    return filepath


async def send_snapshot(chat_id: int, bot, source, prefix: str, label: str, use_ffmpeg: bool = False):
    photo_path = capture_from_source(source, prefix, use_ffmpeg=use_ffmpeg)
    with open(photo_path, "rb") as photo_file:
        await bot.send_photo(
            chat_id=chat_id,
            photo=photo_file,
            caption=f"{label}\nFile: {photo_path.name}"
        )
    return photo_path


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        INITIAL_MESSAGE,
        reply_markup=build_main_menu()
    )


async def foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Scegli quale camera usare:",
        reply_markup=build_main_menu()
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    try:
        if q.data == "shot_local":
            await q.edit_message_text("📸 Scatto da webcam locale in corso...")
            await send_snapshot(
                chat_id=q.message.chat_id,
                bot=context.bot,
                source=0,
                prefix="webcam",
                label="📸 Snapshot webcam locale"
            )
            await q.edit_message_text(
                "Snapshot webcam inviato correttamente.",
                reply_markup=build_back_menu()
            )

        elif q.data == "shot_cam1":
            await q.edit_message_text("🏠 Snapshot da IP Cam 1 in corso...")
            await send_snapshot(
                chat_id=q.message.chat_id,
                bot=context.bot,
                source=RTSP_CAM_1,
                prefix="cam1",
                label="🏠 Snapshot IP Cam 1",
                use_ffmpeg=True
            )
            await q.edit_message_text(
                "Snapshot IP Cam 1 inviato correttamente.",
                reply_markup=build_back_menu()
            )

        elif q.data == "shot_cam2":
            await q.edit_message_text("🚪 Snapshot da IP Cam 2 in corso...")
            await send_snapshot(
                chat_id=q.message.chat_id,
                bot=context.bot,
                source=RTSP_CAM_2,
                prefix="cam2",
                label="🚪 Snapshot IP Cam 2",
                use_ffmpeg=True
            )
            await q.edit_message_text(
                "Snapshot IP Cam 2 inviato correttamente.",
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

    except Exception as e:
        await q.edit_message_text(
            f"Errore: {e}",
            reply_markup=build_back_menu()
        )


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("foto", foto))
    app.add_handler(CallbackQueryHandler(on_button))
    app.run_polling()


if __name__ == "__main__":
    main()