import os
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from reportlab.pdfgen import canvas

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ---------------- DATABASE ----------------

def crea_tabelle():
    conn = sqlite3.connect("volley.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS atleti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        cognome TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS pagamenti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        atleta_id INTEGER,
        importo REAL,
        scadenza TEXT,
        pagato INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS presenze (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        atleta_id INTEGER,
        data TEXT
    )
    """)

    conn.commit()
    conn.close()


def get_conn():
    return sqlite3.connect("volley.db")


# ---------------- ATLETI ----------------

def aggiungi_atleta_db(nome, cognome):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO atleti (nome, cognome) VALUES (?, ?)", (nome, cognome))
    conn.commit()
    conn.close()


def lista_atleti_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, nome, cognome FROM atleti")
    dati = c.fetchall()
    conn.close()
    return dati


# ---------------- PAGAMENTI ----------------

def aggiungi_pagamento_db(atleta_id, importo, scadenza):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO pagamenti (atleta_id, importo, scadenza)
        VALUES (?, ?, ?)
    """, (atleta_id, importo, scadenza))
    conn.commit()
    conn.close()


def lista_debiti():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT a.nome, a.cognome, p.importo, p.scadenza
        FROM pagamenti p
        JOIN atleti a ON a.id = p.atleta_id
        WHERE p.pagato = 0
    """)
    dati = c.fetchall()
    conn.close()
    return dati


# ---------------- PRESENZE ----------------

def aggiungi_presenza_db(atleta_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO presenze (atleta_id, data)
        VALUES (?, ?)
    """, (atleta_id, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()


# ---------------- PDF ----------------

def genera_pdf():
    file = "/tmp/report_mensile.pdf"
    c = canvas.Canvas(file)

    c.drawString(100, 800, "REPORT MENSILE VOLLEY")

    y = 760

    conn = sqlite3.connect("volley.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT a.nome, a.cognome, SUM(p.importo)
        FROM pagamenti p
        JOIN atleti a ON a.id = p.atleta_id
        WHERE p.pagato = 0
        GROUP BY a.id
    """)

    debiti = cur.fetchall()

    c.drawString(100, y, "DEBITI:")
    y -= 30

    if not debiti:
        c.drawString(100, y, "Nessun debito 🎉")
        y -= 20

    for d in debiti:
        c.drawString(100, y, f"{d[0]} {d[1]} - {d[2]} €")
        y -= 20

    conn.close()
    c.save()

    return file


# ---------------- COMANDI BOT ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏐 Bot volley attivo!")


async def aggiungi_atleta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Uso: /aggiungi_atleta Nome Cognome")
        return

    aggiungi_atleta_db(args[0], args[1])
    await update.message.reply_text("Atleta aggiunto!")


async def lista_atleti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    atleti = lista_atleti_db()
    testo = "\n".join([f"{a[0]} - {a[1]} {a[2]}" for a in atleti])
    await update.message.reply_text(testo)


async def debiti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dati = lista_debiti()
    if not dati:
        await update.message.reply_text("Nessun debito 🎉")
        return

    testo = ""
    for d in dati:
        testo += f"{d[0]} {d[1]} - {d[2]}€ scade {d[3]}\n"

    await update.message.reply_text(testo)


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = genera_pdf()
    await update.message.reply_document(document=open(file, "rb"))


# ---------------- BOT ----------------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("aggiungi_atleta", aggiungi_atleta))
app.add_handler(CommandHandler("lista_atleti", lista_atleti))
app.add_handler(CommandHandler("debiti", debiti))
app.add_handler(CommandHandler("report", report))

crea_tabelle()

print("BOT AVVIATO")

app.run_polling()
