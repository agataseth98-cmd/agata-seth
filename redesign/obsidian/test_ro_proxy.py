import importlib.util
import os
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ro_proxy_teste", AQUI / "ro_proxy.py")
mod = importlib.util.module_from_spec(spec)
os.environ.setdefault("OBS_VAULT", str(AQUI))
spec.loader.exec_module(mod)


def vault(tmp_path):
    raiz = Path(tmp_path) / "vault"
    (raiz / "sub").mkdir(parents=True)
    (raiz / ".oculto").mkdir()
    (raiz / "vazio").mkdir()
    (raiz / "a.md").write_text("a", encoding="utf-8")
    (raiz / "sub" / "b.md").write_text("b", encoding="utf-8")
    (raiz / ".oculto" / "c.md").write_text("c", encoding="utf-8")
    (Path(tmp_path) / "fora.md").write_text("f", encoding="utf-8")
    (raiz / "link-fora").symlink_to(Path(tmp_path) / "fora.md")
    mod.VAULT = os.path.realpath(raiz)
    return raiz


def test_lista_a_raiz_e_um_subdiretorio_sem_ocultos_vazios_nem_links_para_fora(tmp_path):
    vault(tmp_path)
    codigo, corpo = mod._listar_disco("/vault/")
    assert codigo == 200 and corpo["files"] == ["a.md", "sub/"]
    codigo, corpo = mod._listar_disco("/vault/sub/")
    assert codigo == 200 and corpo["files"] == ["b.md"]


def test_recusa_caminho_oculto_e_saida_do_vault(tmp_path):
    vault(tmp_path)
    assert mod._listar_disco("/vault/.oculto/")[0] == 403
    assert mod._listar_disco("/vault/../")[0] == 403
    assert mod._listar_disco("/vault/sub/../../")[0] == 403
    assert mod._listar_disco("/vault/%2e%2e/")[0] == 403


def test_arquivo_ou_inexistente_repassa_ao_plugin(tmp_path):
    vault(tmp_path)
    assert mod._listar_disco("/vault/a.md") is None
    assert mod._listar_disco("/vault/nao-existe/") is None
