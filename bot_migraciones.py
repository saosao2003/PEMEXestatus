import openpyxl
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta

TOKEN = "8261058843:AAFEGmNVrrxon3n4fJ6nc5DAXaULcSiNZgE"
META = 266
EXCEL_FILE = "./avance.xlsx"


# ===== LEER EXCEL =====

def cargar_datos():

    wb = openpyxl.load_workbook(EXCEL_FILE)
    sheet = wb.active

    registros = []

    for row in sheet.iter_rows(min_row=2, values_only=True):

        if row[0] and row[1]:

            fecha = datetime.strptime(str(row[0]), "%d/%m/%Y")
            migrados = int(row[1])

            registros.append((fecha, migrados))

    return registros


# ===== HOY =====

def comando_hoy():

    datos = cargar_datos()

    if not datos:
        return "Sin datos"

    fecha, migrados = datos[-1]

    porcentaje = (migrados / META) * 100

    return f"""
📅 Último registro: {fecha.strftime("%d-%b-%Y")}

Migrados: {migrados}
Avance: {porcentaje:.2f}%
"""


# ===== AVANCE =====

def comando_avance():

    datos = cargar_datos()

    if not datos:
        return "Sin datos"

    migrados = datos[-1][1]

    porcentaje = (migrados / META) * 100
    faltan = META - migrados

    return f"""
📊 AVANCE

{migrados}/{META}
{porcentaje:.2f}%
Faltan: {faltan}
"""


# ===== SEMANA =====

def comando_semana():

    datos = cargar_datos()

    hoy = datetime.now()
    inicio = hoy - timedelta(days=hoy.weekday())

    texto = "📅 Semana actual\n\n"

    for fecha, migrados in datos:

        if fecha >= inicio:
            texto += f"{fecha.strftime('%d-%b')}: {migrados}\n"

    return texto


# ===== TELEGRAM =====

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):

    texto = update.message.text.lower()

    if texto == "hoy":
        await update.message.reply_text(comando_hoy())

    elif texto == "avance":
        await update.message.reply_text(comando_avance())

    elif texto == "semana":
        await update.message.reply_text(comando_semana())

    else:
        await update.message.reply_text(
            "Comandos:\n\nhoy\navance\nsemana"
        )


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT, responder))

print("Bot simple corriendo 🚀")

app.run_polling()
