from fastapi import FastAPI, HTTPException, Request, Form
from pydantic import BaseModel
import os
from twilio.rest import Client
import base64
import hashlib
import logging
import datetime
import openai  # OpenAI per GPT-4

app = FastAPI()

# Configura logging per debug
logging.basicConfig(level=logging.INFO)

# Recupera credenziali da variabili d'ambiente
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")  # Numero Twilio

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # API Key per OpenAI GPT-4

if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_WHATSAPP_NUMBER:
    logging.error("Errore: Variabili d'ambiente di Twilio mancanti!")
    raise ValueError("Configurazione Twilio non valida")

if not OPENAI_API_KEY:
    logging.error("Errore: API Key di OpenAI mancante!")
    raise ValueError("API Key OpenAI non trovata")

# Inizializza il client Twilio
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def hash_protect(data: str) -> str:
    """Genera un hash SHA-256 codificato in base64 per protezione"""
    return base64.b64encode(hashlib.sha256(data.encode()).digest()).decode()

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

# Funzione per chiamare GPT-4 e generare una risposta
def genera_risposta_ai(messaggio_utente):
    prompt = f"""
    Sei un chatbot esperto nel calcolo dei preventivi per artigiani. 
    Rispondi in modo professionale e chiaro. Se l'utente chiede un preventivo, guida la conversazione chiedendo:
    1️⃣ Quante ore di lavoro sono necessarie?
    2️⃣ Qual è il costo stimato dei materiali?
    3️⃣ Il lavoro è semplice, medio o complesso?

    Ecco il messaggio dell'utente: {messaggio_utente}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=200,
            api_key=OPENAI_API_KEY,
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"Errore chiamata API OpenAI: {e}")
        return "⚠️ Si è verificato un errore nel generare la risposta. Riprova più tardi!"

# @app.post("/calcola_preventivo/")
# def calcola(preventivo: PreventivoRequest):
#    try:
#        prezzo_finale = calcola_preventivo(preventivo.ore_lavoro, preventivo.materiali_costo, preventivo.complessita)
#        return {"prezzo_preventivato": prezzo_finale, "data": datetime.date.today().isoformat()}
#    except Exception as e:
#        raise HTTPException(status_code=500, detail=str(e))

@app.post("/whatsapp/")
async def whatsapp_webhook(request: Request):
    try:
        form_data = await request.form()
        logging.info(f"Data ricevuta: {form_data}")

        sender = form_data.get("From")
        logging.info(f"Messaggio ricevuto da: {sender}")
        message_body = form_data.get("Body", "").strip().lower()

 
        if not sender.startswith("whatsapp:"):
            logging.error(f"Numero mittente non valido: {sender}")
            raise HTTPException(status_code=400, detail="Il numero deve essere un contatto WhatsApp valido")
        
        if not sender:
            logging.error("Parametro 'From' mancante nella richiesta")
            raise HTTPException(status_code=400, detail="Parametro 'From' mancante")

        risposta = "Ciao! 😊 Sono il tuo assistente per i preventivi. Dimmi, di che lavoro hai bisogno? ✨"
        
        if "preventivo" in message_body:
            risposta = (
                "Ottima scelta! 💪 Per darti un preventivo preciso, ho bisogno di alcune info:\n"
                "1️⃣ Quante ore di lavoro pensi siano necessarie?\n"
                "2️⃣ Qual è il costo stimato dei materiali?\n"
                "3️⃣ Il lavoro è semplice, medio o complesso?"
            )

        # Invio del messaggio tramite Twilio
            client.messages.create(
          #  from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",  
            from_="whatsapp:+14155238886",  # Numero ufficiale di Twilio Sandbox
            body=risposta,  
            to=sender  
        )

        return {"status": "Messaggio inviato", "hash": hash_protect(risposta)}
    
    except Exception as e:
        logging.error(f"Errore nel webhook: {e}")
        raise HTTPException(status_code=500, detail="Errore interno del server")
