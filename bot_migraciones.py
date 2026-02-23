import os
import asyncio
import logging
from datetime import datetime

import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ==============================
# CONFIGURACION
# ==============================

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

EXCEL_FILE = "migraciones.xlsx"

# ==============================
# LOGGING
# ==============================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ==============================
# CARGAR EXCEL
# ==============================

def cargar_excel():
    try:
        df = pd.read_excel(EXCEL_FILE)
        df.columns = df.columns.str.upper().str.strip()
        return df
    except Exception as e:
        logging.error(f"Error cargando Excel: {e}")
        return pd.DataFrame()

# ==============================
# RESUMEN GENERAL
# ==============================

def resumen_general():
    df = cargar_excel()

    if df.empty:
        return "⚠ No hay datos cargados."

    total = len(df)
    completados = len(df[df["ESTADO"] == "COMPLETADO"])
    pendientes = total - completados
    avance = (completados / total) * 100

    return f"""
📊 RESUMEN MIGRACIONES

Total: {total}
Completados: {completados}
Pendientes: {pendientes}

Avance: {avance:.2f}%
"""

# ==============================
# BUSQUEDA GENERICA
# ==============================

def buscar(valor):
    df = cargar_excel()

    if df.empty:
        return "No hay datos."

    resultado = df[
        (df["IP"].astype(str) == valor) |
        (df["SERIE"].astype(str) == valor) |
        (df["SEDE"].astype(str).str.upper() == valor.upper())
    ]

    if resultado.empty:
        return "No encontrado."

    fila = resultado.iloc[0]

    return f"""
🔎 RESULTADO

IP: {fila['IP']}
Serie: {fila['SERIE']}
Sede: {fila['SEDE']}
Estado: {fila['ESTADO']}
"""

# ==============================
# COMANDOS TELEGRAM
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot Migraciones Activo")

async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = resumen_general()
    await update.message.reply_text(mensaje)

async def consulta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usa: /buscar valor")
        return

    valor = context.args[0]
    mensaje = buscar(valor)
    await update.message.reply_text(mensaje)

# ==============================
# ENVIO AUTOMATICO DIARIO
# ==============================

async def envio_diario(app):
    mensaje = resumen_general()
    await app.bot.send_message(chat_id=CHAT_ID, text=mensaje)

# ==============================
# MAIN
# ==============================

scheduler = AsyncIOScheduler()

async def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("resumen", resumen))
    app.add_handler(CommandHandler("buscar", consulta))

    scheduler.add_job(
        envio_diario,
        "cron",
        hour=20,
        minute=0,
        args=[app]
    )

    scheduler.start()

    print("Bot iniciado correctamente")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
