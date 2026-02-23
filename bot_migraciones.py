import gspread
import os
import json
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

META = 266

# ===== GOOGLE SHEETS =====

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

cred_json = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

creds = Credentials.from_service_account_info(
    cred_json,
    scopes=scope
)

client = gspread.authorize(creds)

sheet = client.open_by_key(
    "1xCqKEGKDqyfvFl7z4Fgy8pv2Js6ra1MfZAR5mS344A4"
).sheet1

# ===== CARGAR DATOS SIN PANDAS =====

def cargar_datos():
    data = sheet.get_all_records()

    fechas = []
    migrados = []

    for fila in data:
        fechas.append(datetime.strptime(fila["Fecha"], "%d/%m/%Y"))
        migrados.append(int(fila["Migrados"]))

    return fechas, migrados

# ===== KPI =====

def calcular_kpi():

    fechas, migrados = cargar_datos()

    ultimo = migrados[-1]

    porcentaje = (ultimo / META) * 100

    faltan = META - ultimo

    incrementos = [
        migrados[i] - migrados[i - 1]
        for i in range(1, len(migrados))
    ]

    promedio = sum(incrementos) / len(incrementos) if incrementos else 0

    if promedio > 0:
        dias_restantes = faltan / promedio
        fecha_estimada = datetime.now() + timedelta(days=dias_restantes)
        fecha_estimada = fecha_estimada.strftime("%d-%b-%Y")
    else:
        fecha_estimada = "Sin cálculo"

    return ultimo, porcentaje, faltan, promedio, fecha_estimada

# ===== REPORTE =====

def crear_reporte():

    migrados, porcentaje, faltan, promedio, fecha_estimada = calcular_kpi()

    return f"""
📊 REPORTE DIARIO 20:00

Migrados: {migrados}/{META}
Avance: {porcentaje:.2f}%
Faltan: {faltan}

Promedio diario: {promedio:.2f}

Meta estimada: {fecha_estimada}
"""

# ===== TELEGRAM HANDLER =====

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):

    texto = update.message.text.lower()

    if texto == "avance":

        await update.message.reply_text(crear_reporte())

    elif texto == "hoy":

        migrados, porcentaje, _, _, _ = calcular_kpi()

        await update.message.reply_text(
            f"""
📅 Hoy

Migrados: {migrados}
Avance: {porcentaje:.2f}%
"""
        )

    elif texto == "proyeccion":

        _, _, _, promedio, fecha_estimada = calcular_kpi()

        await update.message.reply_text(
            f"Meta estimada: {fecha_estimada}\nPromedio: {promedio:.2f}/día"
        )

# ===== MAIN =====

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT, responder))

# ===== SCHEDULER =====

scheduler = AsyncIOScheduler(timezone="America/Mexico_City")

async def enviar_reporte_auto():
    await app.bot.send_message(chat_id=CHAT_ID, text=crear_reporte())

scheduler.add_job(
    enviar_reporte_auto,
    "cron",
    hour=20,
    minute=0
)

scheduler.start()

print("Bot optimizado corriendo 24/7 🚀")

app.run_polling()
