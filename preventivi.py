from fastapi import FastAPI, HTTPException, Request, Form
from pydantic import BaseModel
import datetime
import os
from twilio.rest import Client
import base64
import hashlib

app = FastAPI()

# Config Twilio (prendi i dati dal tuo account Twilio)
TWILIO_ACCOUNT_SID = "your_account_sid"
TWILIO_AUTH_TOKEN = "your_auth_token"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"  # Numero Twilio
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Simuliamo un database locale per i prezzi medi
COSTO_ORARIO_BASE = 30  # Euro/ora (valore medio, può essere aggiornato con i dati raccolti)
MARGINE_PROFITTO = 1.2  # Margine di profitto standard (20%)

# Funzione di hashing per proteggere il codice da copia
def hash_protect(data):
    return base64.b64encode(hashlib.sha256(data.encode()).digest()).decode()

# Modello dati per la richiesta di preventivo
class PreventivoRequest(BaseModel):
    ore_lavoro: float
    materiali_costo: float
    complessita: int  # 1 = facile, 2 = medio, 3 = complesso

# Funzione per calcolare il preventivo
def calcola_preventivo(ore_lavoro: float, materiali_costo: float, complessita: int):
    costo_base = ore_lavoro * COSTO_ORARIO_BASE
    
    # Aggiustamento in base alla complessità
    fattore_complessita = {1: 1.0, 2: 1.2, 3: 1.5}
    costo_totale = (costo_base + materiali_costo) * fattore_complessita.get(complessita, 1.0)
    costo_totale *= MARGINE_PROFITTO
    
    return round(costo_totale, 2)

@app.post("/calcola_preventivo/")
def calcola(preventivo: PreventivoRequest):
    try:
        prezzo_finale = calcola_preventivo(preventivo.ore_lavoro, preventivo.materiali_costo, preventivo.complessita)
        return {"prezzo_preventivato": prezzo_finale, "data": datetime.date.today().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint per ricevere messaggi WhatsApp da Twilio
@app.post("/whatsapp/")
async def whatsapp_webhook(request: Request):
    form_data = await request.form()
    sender = form_data.get("From")
    message_body = form_data.get("Body").strip().lower()
    
    risposta = "Ciao! 😊 Sono il tuo assistente per i preventivi. Dimmi, di che lavoro hai bisogno? ✨"
    
    if "preventivo" in message_body:
        risposta = "Ottima scelta! 💪 Per darti un preventivo preciso, ho bisogno di alcune info:\n1️⃣ Quante ore di lavoro pensi siano necessarie?\n2️⃣ Qual è il costo stimato dei materiali?\n3️⃣ Il lavoro è semplice, medio o complesso?"
    
    # Protezione anti-spam (es. limiti di richieste dallo stesso numero)
    if sender is None or not sender.startswith("whatsapp:"):
        raise HTTPException(status_code=400, detail="Richiesta non valida")
    
    client.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        body=risposta,
        to=sender
    )
    
    return {"status": "Messaggio inviato", "hash": hash_protect(risposta)}
