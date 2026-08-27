import os
import json
import shutil
import datetime
from typing import List, Dict, Any, Optional

class MemoryCore:
    def __init__(self, base_dir: str = os.path.expanduser("~/.agata_il")):
        self.base_dir = base_dir
        self.memoria_dir = os.path.join(base_dir, "memoria")
        self.propostas_dir = os.path.join(self.memoria_dir, "propostas")
        self.backup_dir = os.path.join(base_dir, "backup_emergencia")
        for d in [self.memoria_dir, self.propostas_dir, self.backup_dir]:
            os.makedirs(d, exist_ok=True)
        self.paths = {
            "semantic": os.path.join(self.memoria_dir, "semantic.json"),
            "episodic": os.path.join(self.memoria_dir, "episodic.json"),
            "procedural": os.path.join(self.memoria_dir, "procedural.json"),
            "overlay": os.path.join(self.memoria_dir, "overlay_ontologico.json")
        }

    def _safe_load(self, filepath: str, default: Any = None) -> Any:
        if default is None:
            default = {}
        if not os.path.exists(filepath):
            return default
        try:
            if os.path.getsize(filepath) < 50:
                raise ValueError("Stub/corrompido")
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            backup_path = os.path.join(self.backup_dir, f"{os.path.basename(filepath)}.bak{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
            shutil.copy2(filepath, backup_path)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=2, ensure_ascii=False)
            return default

    def _save_json(self, filepath: str, data: Any):
        temp_path = filepath + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, filepath)

    def add_semantic_fact(self, fato: str, confianca: float = 0.8, origem: str = "IB") -> bool:
        data = self._safe_load(self.paths["semantic"], {"fatos": []})
        data["fatos"].append({
            "id": f"FACT_{datetime.datetime.now().strftime('%Y%m%d_%H]%M%S%f')}",
            "fato": fato,
            "confianca": confianca,
            "origem": origem,
            "timestamp": datetime.datetime.now().isoformat()
        })
        self._save_json(self.paths["semantic"], data)
        return True

    def get_semantic_facts(self, query: Optional[str] = None) -> List[Dict]:
        data = self._safe_load(self.paths["semantic"], {"fatos": []})
        fatos = data.get("fatos", [])
        if query:
            q = query.lower()
            return [f for f in fatos if q in f["fato"].lower()]
        return fatos

    def add_episodic_event(self, evento: str, limite: int = 10) -> bool:
        data = self._safe_load(self.paths["episodic"], {"eventos": []})
        data["eventos"].append({
            "evento": evento,
            "timestamp": datetime.datetime.now().isoformat()
        })
        data["eventos"] = data["eventos"][-limite:]
        self._save_json(self.paths["episodic"], data)
        return True

    def get_episodic_history(self) -> List[Dict]:
        return self._safe_load(self.paths["episodic"], {"eventos": []}).get("eventos", [])

    def propose_canonical_change(self, doc_name: str, proposed_content: str) -> str:
        safe_name = "".join(c for c in doc_name if c.isalnum() or c in ("-", "_", "."))
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.propostas_dir, f"PROPOSTA_{safe_name}_{ts}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# PROPOSTA DE ALTERAÇÃO CANÎNICA \nDocumento: {doc_name}\nData: {datetime.datetime.now().isoformat()}\nStatus: AGUARDANDO RATIFICAçãO DA IB (!SUDO)\n\n--- CONTEÚDO ---\n\n{proposed_content}")
        return path