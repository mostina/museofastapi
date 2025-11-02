from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime
import os
import uvicorn

# ✅ Connessione a MongoDB Atlas
MONGO_URI = "mongodb+srv://museomagazzino:artwork@cluster0.kedecnn.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["MuseoMagazzino"]
artworks_collection = db["artworks"]
iot_collection = db["iot-data"]

app = FastAPI(title="Museo Smart System API")

# ==========================
# 📦 MODELLI
# ==========================

class ArtWork(BaseModel):
    _id: str
    nome: str
    autore: str
    anno: int
    in_prestito: bool
    in_magazzino: bool

class IoTData(BaseModel):
    _id: str
    latitude: float
    longitude: float
    temperature: float
    humidity: float
    timestamp: str

# ==========================
# 🏛️ ENDPOINT OPERE D’ARTE
# ==========================

@app.get("/artworks")
def get_all_artworks():
    """Ritorna tutte le opere nel database."""
    data = list(artworks_collection.find({}, {"_id": 0}))
    return {"count": len(data), "artworks": data}

@app.post("/artworks/add")
def add_artwork(artwork: ArtWork):
    """Aggiunge una nuova opera."""
    if artworks_collection.find_one({"_id": artwork._id}):
        raise HTTPException(status_code=400, detail="Opera già esistente")
    artworks_collection.insert_one(artwork.dict())
    return {"message": f"Opera '{artwork.nome}' aggiunta con successo!"}

@app.delete("/artworks/{artwork_id}")
def delete_artwork(artwork_id: str):
    """Rimuove un'opera tramite ID."""
    result = artworks_collection.delete_one({"_id": artwork_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Opera non trovata")
    return {"message": f"Opera {artwork_id} rimossa con successo"}

# ==========================
# 🌡️ ENDPOINT IoT (dal simulatore)
# ==========================

@app.get("/iot-data")
def get_iot_data():
    """Ritorna tutti i dati IoT presenti nel database."""
    data = list(iot_collection.find({}, {"_id": 0}))  # esclude l'_id ObjectId generato da MongoDB
    return {"count": len(data), "iot_data": data}

@app.post("/iot-data/update")
def update_iot_data(data: IoTData):
    """Aggiorna sempre i dati IoT per ogni opera."""
    print("📡 Ricevuti dati IoT:", data.dict())  # log per debug

    artwork = artworks_collection.find_one({"_id": data._id})

    if not artwork:
        raise HTTPException(status_code=404, detail=f"Opera {data._id} non trovata")

    try:
        # Aggiorna o inserisci sempre i dati IoT
        iot_collection.update_one(
            {"_id": data._id},
            {"$set": data.dict()},
            upsert=True
        )
        return {"message": f"Dati IoT aggiornati per {data._id}"}
    except Exception as e:
        print("❌ Errore durante l'update IoT:", e)
        raise HTTPException(status_code=500, detail="Errore interno durante l'update IoT")


# ==========================
# 🧠 TEST ROUTE
# ==========================

@app.get("/")
def root():
    return {"message": "Museo Smart System API attiva 🚀"}

# ==========================
# 🏁 START SERVER
# ==========================


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # fallback su 10000 se non definita
    uvicorn.run("main:app", host="0.0.0.0", port=port)
