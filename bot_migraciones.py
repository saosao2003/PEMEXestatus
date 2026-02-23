import logging
import asyncio
import os
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt

import gspread
from google.oauth2.service_account import Credentials

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ==============================
# CONFIGURACION
# ==============================

TOKEN = os.getenv("BOT_TOKEN")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SPREADSHEET_NAME = "Migraciones"

# ==============================
# LOGGING
# ==============================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ==============================
# GOOGLE SHEETS CONEXION
# ==============================

def conectar_google_sheets():

    creds = Credentials.from_service_account_file(
        "credenciales.json",
        scopes=SCOPES
    )

    client = gspread.authorize(creds)

    sheet = client.open(SPREADSHEET_NAME).sheet1

    return sheet


# ==============================
# LEER DATOS
# ==============================

def obtener_datos():

    sheet = conectar_google_sheets()

    data = sheet.get_all_records()

    df = pd.DataFrame(data)

    return df


# ==============================
# CALCULAR ESTADO
# ==============================

def calcular_estado():

    df = obtener_datos()

    total = len(df)

    if total == 0:
        return "Sin registros"

    completados = len(df[df["Estado"] == "COMPLETADO"])

    porcentaje = (completados / total) * 100

    return f"""
Estado Migraciones

Total: {total}
Completados: {completados}
Pendientes: {total - completados}

Avance: {porcentaje:.2f}%
"""


# ==============================
# GENERAR GRAFICA
# ==============================

def generar_grafica():

    df = obtener_datos()

    conteo = df["Estado"].value_counts()

    plt.figure()

    conteo.plot(kind="bar")

    archivo = "grafica.png"

    plt.savefig(archivo)

    plt.close()

    return archivo


# ==============================
# COMANDOS TELEGRAM
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Bot de Migraciones Activo"
    )


async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):

    mensaje = calcular_estado()

    await update.message.reply_text(mensaje)


async def grafica(update: Update, context: ContextTypes.DEFAULT_TYPE):

    archivo = generar_grafica()

    await update.message.reply_photo(
        photo=open(archivo, "rb")
    )


# ==============================
# JOB AUTOMATICO 20:00 HRS
# ==============================

async def envio_automatico(app):

    try:

        chat_id = os.getenv("CHAT_ID")

        mensaje = calcular_estado()

        await app.bot.send_message(
            chat_id=chat_id,
            text=mensaje
        )

    except Exception as e:

        logging.error(e)


# ==============================
# SCHEDULER
# ==============================

scheduler = AsyncIOScheduler()


# ==============================
# MAIN
# ==============================

async def main():

    app = ApplicationBuilder().token(TOKEN).build()

    # handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(CommandHandler("grafica", grafica))

    # scheduler diario 20:00
    scheduler.add_job(
        envio_automatico,
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


# ==============================
# ARRANQUE
# ==============================

if __name__ == "__main__":

    asyncio.run(main())
