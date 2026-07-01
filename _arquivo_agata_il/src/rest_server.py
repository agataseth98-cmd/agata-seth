import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os, sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory_core import MemoryCore

app = FastAPI()
core = MemoryCore()

class FatoReq(BaseModel):
    fato: str
    confianca: float = 0.8
    origem: str = "IC"

class QueryReq(BaseModel):
    query: str

@app.post("/registrar")
def registrar(req: FatoReq) -> dict:
    try:
        core.add_semantic_fact(req.fato, req.confianca, req.origem)
        return {"status": "ok", "msg": "Fato registrado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/consultar")
def consultar(req: QueryReq) -> dict:
    try:
        fatos = core.get_semantic_facts(req.query)
        if not fatos:
            return {"status": "ok", "msg": "Nenhum fato"}
        linhas = [f"- [{f['timestamp']}] ({f['confianca']}) {f['fato']}" for f in fatos]
        return {"status": "ok", "msg": "\n".join(linhas)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
