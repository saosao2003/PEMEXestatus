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
# MENU
# =========================

MENU = """
📊 MENU MIGRACIONES

1️⃣ Hoy
2️⃣ Dashboard
3️⃣ Avance
4️⃣ Faltan
5️⃣ Semana actual
6️⃣ Semana pasada
7️⃣ Detalle semana
8️⃣ Proyección
9️⃣ Gráfica

Escribe el número o nombre
"""


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
# CARGAR DATOS
# =========================

def cargar_datos():

    datos = []

    wb = load_workbook(EXCEL_FILE, data_only=True)
    ws = wb.active

    for row in ws.iter_rows(min_row=2, values_only=True):

        try:

            if not row[0]:
                continue

            if isinstance(row[0], str) and "semana" in row[0].lower():
                continue

            fecha = convertir_fecha(row[0])

            enlaces_telmex = int(row[2] or 0)
            enlaces_totalplay = int(row[3] or 0)

            bal_telmex = int(row[5] or 0)
            bal_totalplay = int(row[6] or 0)

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
# BARRA
# =========================

def barra(p):

    llenos = int(p/5)
    vacios = 20 - llenos

    return "█"*llenos + "░"*vacios


# =========================
# RITMO PROMEDIO
# =========================

def calcular_ritmo():

    datos = cargar_datos()

    if len(datos) < 2:
        return 0,0

    inc_enlaces=[]
    inc_bal=[]

    for i in range(1,len(datos)):

        inc_enlaces.append(
            datos[i]["enlaces"] - datos[i-1]["enlaces"]
        )

        inc_bal.append(
            datos[i]["balanceadores"] - datos[i-1]["balanceadores"]
        )

    prom_enlaces = sum(inc_enlaces)/len(inc_enlaces)
    prom_bal = sum(inc_bal)/len(inc_bal)

    return prom_enlaces, prom_bal


# =========================
# HOY
# =========================

def comando_hoy():

    datos = cargar_datos()

    if not datos:
        return "Sin datos"

    d = datos[-1]

    porc_enlaces = d["enlaces"]/META_ENLACES*100
    porc_bal = d["balanceadores"]/META_BALANCEADORES*100

    ritmo_enlaces, ritmo_bal = calcular_ritmo()

    return f"""
📅 {d["fecha"].strftime("%d-%b-%Y")}

🔹 ENLACES
Total Migrados: {d["enlaces"]}
Telmex: {d["enlaces_telmex"]}
Totalplay: {d["enlaces_totalplay"]}

Avance: {porc_enlaces:.2f}%
Ritmo promedio: {ritmo_enlaces:.2f} por día

⚖️ BALANCEADORES
Total Instalados: {d["balanceadores"]}
Telmex: {d["bal_telmex"]}
Totalplay: {d["bal_totalplay"]}

Avance: {porc_bal:.2f}%
Ritmo promedio: {ritmo_bal:.2f} por día
"""


# =========================
# DASHBOARD
# =========================

def comando_dashboard():

    datos=cargar_datos()

    d=datos[-1]

    porc_enlaces=d["enlaces"]/META_ENLACES*100
    porc_bal=d["balanceadores"]/META_BALANCEADORES*100

    return f"""
📊 DASHBOARD MIGRACIONES

Fecha: {d["fecha"].strftime("%d-%b-%Y")}

ENLACES
{d["enlaces"]}/{META_ENLACES}
{barra(porc_enlaces)}
{porc_enlaces:.2f}%

BALANCEADORES
{d["balanceadores"]}/{META_BALANCEADORES}
{barra(porc_bal)}
{porc_bal:.2f}%
"""
# =========================
# RESTO COMANDOS
# =========================

def comando_avance():
    return comando_dashboard()


def comando_faltan():

    d=cargar_datos()[-1]

    return f"""
Faltan enlaces: {META_ENLACES-d["enlaces"]}
Faltan balanceadores: {META_BALANCEADORES-d["balanceadores"]}
"""


def comando_proyeccion():

    datos=cargar_datos()

    prom_enlaces,prom_bal=calcular_ritmo()

    faltan_enlaces=META_ENLACES-datos[-1]["enlaces"]
    faltan_bal=META_BALANCEADORES-datos[-1]["balanceadores"]

    fecha_enlaces=datetime.now()+timedelta(days=faltan_enlaces/prom_enlaces if prom_enlaces else 0)
    fecha_bal=datetime.now()+timedelta(days=faltan_bal/prom_bal if prom_bal else 0)

    return f"""
📅 PROYECCION

Enlaces: {fecha_enlaces.strftime("%d-%b-%Y")}
Balanceadores: {fecha_bal.strftime("%d-%b-%Y")}
"""


# =========================
# GRAFICA
# =========================

def generar_grafica():

    datos=cargar_datos()

    fechas=[d["fecha"] for d in datos]
    enlaces=[d["enlaces"] for d in datos]
    bal=[d["balanceadores"] for d in datos]

    plt.figure()

    plt.plot(fechas,enlaces)
    plt.plot(fechas,bal)

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

    if t in ["1","hoy"]:
        await update.message.reply_text(comando_hoy())

    elif t in ["2","dashboard"]:
        await update.message.reply_text(comando_dashboard())

        archivo=generar_grafica()

        await update.message.reply_photo(photo=open(archivo,"rb"))

    elif t in ["3","avance"]:
        await update.message.reply_text(comando_avance())

    elif t in ["4","faltan"]:
        await update.message.reply_text(comando_faltan())

    elif t in ["8","proyeccion"]:
        await update.message.reply_text(comando_proyeccion())

    elif t in ["9","grafica"]:

        archivo=generar_grafica()

        await update.message.reply_photo(photo=open(archivo,"rb"))

    else:
        await update.message.reply_text("Comando no reconocido")

    # SIEMPRE mostrar menu
    await update.message.reply_text(MENU)


# =========================
# HEALTHCHECK
# =========================

class HealthCheck(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")


def run_health():
    server = HTTPServer(("0.0.0.0",10000),HealthCheck)
    server.serve_forever()


# =========================
# RUN
# =========================

app=ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT,responder))

threading.Thread(target=run_health,daemon=True).start()

print("BOT ACTIVO")

app.run_polling(drop_pending_updates=True)
