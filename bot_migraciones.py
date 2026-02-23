import os
import json
import gspread
import threading
from datetime import datetime, timedelta
from flask import Flask
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ================= CONFIG =================

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
META = 266

# ================= GOOGLE SHEETS =================

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

# ================= FUNCIONES =================

def cargar_datos():
    data = sheet.get_all_records()
    fechas = []
    migrados = []

    for fila in data:
        fechas.append(datetime.strptime(fila["Fecha"], "%d/%m/%Y"))
        migrados.append(int(fila["Migrados"]))

    return fechas, migrados


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


# ================= TELEGRAM =================

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.lower()

    if texto == "avance":
        await update.message.reply_text(crear_reporte())

    elif texto == "hoy":
        migrados, porcentaje, _, _, _ = calcular_kpi()
        await update.message.reply_text(
            f"📅 Hoy\n\nMigrados: {migrados}\nAvance: {porcentaje:.2f}%"
        )

    elif texto == "proyeccion":
        _, _, _, promedio, fecha_estimada = calcular_kpi()
        await update.message.reply_text(
            f"Meta estimada: {fecha_estimada}\nPromedio: {promedio:.2f}/día"
        )


# ================= APP =================

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

# ================= SCHEDULER =================

scheduler = AsyncIOScheduler(timezone="America/Mexico_City")

async def enviar_reporte_auto():
    await app.bot.send_message(chat_id=CHAT_ID, text=crear_reporte())

scheduler.add_job(enviar_reporte_auto, "cron", hour=20, minute=0)
scheduler.start()

# ================= FLASK (PARA RENDER GRATIS) =================

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot activo 🚀"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web).start()

# ================= START =================

print("Bot optimizado funcionando 24/7 🚀")
app.run_polling()
