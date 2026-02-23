import os
import logging
import asyncio
from datetime import datetime

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ==============================
# CONFIGURACIÓN
# ==============================

TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ==============================
# COMANDOS TELEGRAM
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bot activo y funcionando correctamente ✅"
    )


async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(f"Bot activo.\nHora servidor: {now}")


# ==============================
# TAREA PROGRAMADA
# ==============================

async def tarea_programada():
    logger.info("Ejecutando tarea programada...")
    # Aquí puedes agregar lógica
    # Ejemplo: revisar base de datos, enviar alertas, etc.


# ==============================
# MAIN ASYNC
# ==============================

async def main():

    # Crear scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        tarea_programada,
        "interval",
        minutes=5
    )

    scheduler.start()

    # Crear aplicación Telegram
    app = ApplicationBuilder().token(TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("estado", estado))

    logger.info("Bot iniciado correctamente")

    # Iniciar bot
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    # Mantener vivo
    await asyncio.Event().wait()


# ==============================
# ENTRY POINT
# ==============================

if __name__ == "__main__":
    asyncio.run(main())
