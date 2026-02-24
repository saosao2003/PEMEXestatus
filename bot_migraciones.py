import matplotlib.pyplot as plt
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from openpyxl import load_workbook
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# =========================
# CONFIG
# =========================

TOKEN = "8261058843:AAFEGmNVrrxon3n4fJ6nc5DAXaULcSiNZgE"
EXCEL_FILE = "./avance.xlsx"

META_ENLACES = 266
META_BALANCEADORES = 266


# =========================
# CONVERTIR FECHA
# =========================

def convertir_fecha(valor):

    if isinstance(valor, datetime):
        return valor

    valor = str(valor).strip()

    formatos = [
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%d-%b-%Y"
    ]

    for formato in formatos:
        try:
            return datetime.strptime(valor, formato)
        except:
            pass

    raise ValueError(f"Formato fecha no soportado: {valor}")


# =========================
# CARGAR EXCEL ROBUSTO
# =========================

def cargar_datos():

    datos = []

    try:
        wb = load_workbook(EXCEL_FILE, data_only=True)
        ws = wb.active
    except Exception as e:
        print("Error abriendo Excel:", e)
        return []

    for row in ws.iter_rows(min_row=2, values_only=True):

        try:

            if not row[0]:
                continue

            # IGNORAR FILAS SEMANA
            if isinstance(row[0], str) and "semana" in row[0].lower():
                continue

            fecha = convertir_fecha(row[0])

            enlaces_telmex = int(row[2] or 0)
            enlaces_totalplay = int(row[3] or 0)

            bal_telmex = int(row[5] or 0)
            bal_totalplay = int(row[5] or 0)

            datos.append({
                "fecha": fecha,

                "enlaces": enlaces_telmex + enlaces_totalplay,
                "enlaces_telmex": enlaces_telmex,
                "enlaces_totalplay": enlaces_totalplay,

                "balanceadores": bal_telmex + bal_totalplay,
                "bal_telmex": bal_telmex,
                "bal_totalplay": bal_totalplay
            })

        except Exception as e:
            print("Error fila:", row, e)

    wb.close()

    datos.sort(key=lambda x: x["fecha"])

    return datos

# =========================
# BARRA PROGRESO
# =========================

def barra(p):

    llenos = int(p / 5)
    vacios = 20 - llenos

    return "█" * llenos + "░" * vacios


# =========================
# HOY
# =========================

def comando_hoy():

    datos = cargar_datos()

    if not datos:
        return "Sin datos"

    d = datos[-1]

    porc_enlaces = d["enlaces"] / META_ENLACES * 100
    porc_bal = d["balanceadores"] / META_BALANCEADORES * 100

    return f"""
📅 {d["fecha"].strftime("%d-%b-%Y")}

🔹 ENLACES
Total: {d["enlaces"]}
📡 Telmex: {d["enlaces_telmex"]}
🌐 Totalplay: {d["enlaces_totalplay"]}
Avance: {porc_enlaces:.2f}%

⚖️ BALANCEADORES
Total: {d["balanceadores"]}
📡 Telmex: {d["bal_telmex"]}
🌐 Totalplay: {d["bal_totalplay"]}
Avance: {porc_bal:.2f}%
"""


# =========================
# AVANCE
# =========================

def comando_avance():

    datos = cargar_datos()

    if not datos:
        return "Sin datos"

    d = datos[-1]

    porc_enlaces = d["enlaces"] / META_ENLACES * 100
    porc_bal = d["balanceadores"] / META_BALANCEADORES * 100

    return f"""
📊 AVANCE ENLACES
{d["enlaces"]}/{META_ENLACES}
{barra(porc_enlaces)}
{porc_enlaces:.2f}%

⚖️ AVANCE BALANCEADORES
{d["balanceadores"]}/{META_BALANCEADORES}
{barra(porc_bal)}
{porc_bal:.2f}%
"""


# =========================
# DASHBOARD
# =========================

def comando_dashboard():

    datos = cargar_datos()

    if not datos:
        return "Sin datos"

    d = datos[-1]

    porc_enlaces = d["enlaces"] / META_ENLACES * 100
    porc_bal = d["balanceadores"] / META_BALANCEADORES * 100

    faltan_enlaces = META_ENLACES - d["enlaces"]
    faltan_bal = META_BALANCEADORES - d["balanceadores"]

    return f"""
📊 DASHBOARD MIGRACIONES

Fecha: {d["fecha"].strftime("%d-%b-%Y")}

━━━━━━━━━━━━━━━

ENLACES
{d["enlaces"]}/{META_ENLACES}
{barra(porc_enlaces)}
Avance: {porc_enlaces:.2f}%
Faltan: {faltan_enlaces}

Telmex: {d["enlaces_telmex"]}
Totalplay: {d["enlaces_totalplay"]}

━━━━━━━━━━━━━━━

BALANCEADORES
{d["balanceadores"]}/{META_BALANCEADORES}
{barra(porc_bal)}
Avance: {porc_bal:.2f}%
Faltan: {faltan_bal}

Telmex: {d["bal_telmex"]}
Totalplay: {d["bal_totalplay"]}
"""


# =========================
# FALTAN
# =========================

def comando_faltan():

    datos = cargar_datos()

    if not datos:
        return "Sin datos"

    d = datos[-1]

    return f"""
Faltan enlaces: {META_ENLACES - d["enlaces"]}
Faltan balanceadores: {META_BALANCEADORES - d["balanceadores"]}
"""


# =========================
# SEMANA ACTUAL
# =========================

def comando_semana():

    datos = cargar_datos()

    if not datos:
        return "Sin datos"

    hoy = datetime.now()
    inicio = hoy - timedelta(days=hoy.weekday())

    texto = "📅 SEMANA ACTUAL\n\n"

    for d in datos:

        if d["fecha"] >= inicio:

            texto += f'{d["fecha"].strftime("%d-%b")} | E:{d["enlaces"]} B:{d["balanceadores"]}\n'

    return texto


# =========================
# SEMANA PASADA
# =========================

def comando_semana_pasada():

    datos = cargar_datos()

    if not datos:
        return "Sin datos"

    hoy = datetime.now()

    inicio = hoy - timedelta(days=hoy.weekday()+7)
    fin = inicio + timedelta(days=6)

    texto = "📅 SEMANA PASADA\n\n"

    for d in datos:

        if inicio <= d["fecha"] <= fin:

            texto += f'{d["fecha"].strftime("%d-%b")} | E:{d["enlaces"]} B:{d["balanceadores"]}\n'

    return texto


# =========================
# DETALLE SEMANA
# =========================

def comando_detalle_semana():

    datos = cargar_datos()

    if not datos:
        return "Sin datos"

    hoy = datetime.now()
    inicio = hoy - timedelta(days=hoy.weekday())

    primero = None
    ultimo = None

    for d in datos:

        if d["fecha"] >= inicio:

            if primero is None:
                primero = d

            ultimo = d

    if primero and ultimo:

        return f"""
DETALLE SEMANA

Enlaces migrados: {ultimo["enlaces"] - primero["enlaces"]}
Balanceadores migrados: {ultimo["balanceadores"] - primero["balanceadores"]}
"""

    return "Sin datos semana"


# =========================
# PROYECCION
# =========================

def comando_proyeccion():

    datos = cargar_datos()

    if len(datos) < 2:
        return "Sin suficientes datos"

    inc_enlaces = []
    inc_bal = []

    for i in range(1, len(datos)):

        inc_enlaces.append(datos[i]["enlaces"] - datos[i-1]["enlaces"])
        inc_bal.append(datos[i]["balanceadores"] - datos[i-1]["balanceadores"])

    prom_enlaces = sum(inc_enlaces)/len(inc_enlaces)
    prom_bal = sum(inc_bal)/len(inc_bal)

    faltan_enlaces = META_ENLACES - datos[-1]["enlaces"]
    faltan_bal = META_BALANCEADORES - datos[-1]["balanceadores"]

    fecha_enlaces = datetime.now()+timedelta(days=faltan_enlaces/prom_enlaces if prom_enlaces else 0)
    fecha_bal = datetime.now()+timedelta(days=faltan_bal/prom_bal if prom_bal else 0)

    return f"""
PROYECCION

Enlaces: {fecha_enlaces.strftime("%d-%b-%Y")}
Balanceadores: {fecha_bal.strftime("%d-%b-%Y")}
"""


# =========================
# GRAFICA
# =========================

def generar_grafica():

    datos = cargar_datos()

    fechas = [d["fecha"] for d in datos]
    enlaces = [d["enlaces"] for d in datos]
    bal = [d["balanceadores"] for d in datos]

    plt.figure()

    plt.plot(fechas, enlaces)
    plt.plot(fechas, bal)

    plt.title("Avance Migraciones")
    plt.grid()

    archivo="grafica.png"

    plt.savefig(archivo)
    plt.close()

    return archivo


# =========================
# TELEGRAM
# =========================

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):

    t = update.message.text.lower()

    if t=="hoy":
        await update.message.reply_text(comando_hoy())

    elif t=="avance":
        await update.message.reply_text(comando_avance())

    elif t=="dashboard":

        await update.message.reply_text(comando_dashboard())

        archivo = generar_grafica()

        await update.message.reply_photo(photo=open(archivo,"rb"))

    elif t=="faltan":
        await update.message.reply_text(comando_faltan())

    elif t=="semana":
        await update.message.reply_text(comando_semana())

    elif t=="semana pasada":
        await update.message.reply_text(comando_semana_pasada())

    elif t=="detalle semana":
        await update.message.reply_text(comando_detalle_semana())

    elif t=="proyeccion":
        await update.message.reply_text(comando_proyeccion())

    elif t=="grafica":

        archivo=generar_grafica()

        await update.message.reply_photo(photo=open(archivo,"rb"))

    else:

        await update.message.reply_text(
"""
Comandos disponibles:

dashboard
hoy
avance
faltan
semana
semana pasada
detalle semana
proyeccion
grafica
"""
)


# =========================
# HEALTHCHECK RENDER
# =========================

class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health():
    server = HTTPServer(("0.0.0.0", 10000), HealthCheck)
    server.serve_forever()


# =========================
# RUN
# =========================

app = ApplicationBuilder().token(TOKEN).concurrent_updates(False).build()

app.add_handler(MessageHandler(filters.TEXT, responder))

threading.Thread(target=run_health, daemon=True).start()

print("BOT MIGRACIONES ACTIVO")

app.run_polling(drop_pending_updates=True, close_loop=False)
