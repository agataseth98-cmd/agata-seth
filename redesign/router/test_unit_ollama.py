"""Testes das units do Ollama sob demanda (18/11/2026): socket em :11434, proxy ocioso de 15 min, backend na
porta interna :11447 sem [Install] (o padrão do Laya e do Ollaya, conferido por scripts/testar_sob_demanda.py).
Aqui: o que é específico do Ollama (sandbox, GPU, PATH, ~/.ollama), o seth-parar que não acorda o backend, e a
documentação da migração. Só lê arquivos.
Rodar: pytest -q redesign/router/test_unit_ollama.py
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CONFIG = RAIZ / "config"
SYSTEMD = RAIZ / "redesign" / "systemd"
UNIT = CONFIG / "ollama-agata.service"


def _ativas(caminho: Path) -> list[str]:
    return [l.strip() for l in caminho.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.lstrip().startswith("#")]


def test_so_o_socket_fica_no_target_backend_e_proxy_sob_demanda():
    assert "WantedBy=agata.target" in _ativas(CONFIG / "ollama-agata.socket")
    for nome in ("ollama-agata.service", "ollama-agata-proxy.service"):
        ativas = _ativas(CONFIG / nome)
        assert "[Install]" not in ativas and not any(l.startswith("WantedBy=") for l in ativas), nome
        assert "PartOf=agata.target" in ativas
    assert "StopWhenUnneeded=yes" in _ativas(UNIT)
    assert "ListenStream=127.0.0.1:11434" in _ativas(CONFIG / "ollama-agata.socket")


def test_unit_antiga_de_redesign_systemd_saiu():
    assert not (SYSTEMD / "ollama-agata.service").exists()  # a unit vive em config/, como Laya e Ollaya


def test_sandbox_gpu_path_e_diretorios_do_usuario():
    ativas = _ativas(UNIT)
    path = [l for l in ativas if l.startswith("Environment=PATH=")]
    assert len(path) == 1 and "/opt/cuda/bin" in path[0].split("=", 2)[2].split(":")
    assert "ReadWritePaths=-%h/.local/share/ollama" in ativas
    assert "ReadWritePaths=-%h/.ollama" in ativas  # o ollama grava a chave em ~/.ollama
    assert "ExecStartPre=+/usr/bin/mkdir -p %h/.local/share/ollama/models" in ativas
    assert "Environment=OLLAMA_NUM_GPU=999" in ativas and "Environment=CUDA_VISIBLE_DEVICES=0" in ativas
    assert not any(l.startswith("User=") or "sudo" in l or "0.0.0.0" in l for l in ativas)


def test_seth_nao_sobe_o_ollama_e_seth_parar_nao_o_acorda():
    seth = (SYSTEMD / "seth").read_text(encoding="utf-8")
    assert "ollama-agata" not in seth  # entra pelo agata.target (o socket), como os outros sob demanda
    parar = (SYSTEMD / "seth-parar").read_text(encoding="utf-8")
    # `ollama ps` acordaria o backend pelo socket só para descarregar modelos: só pergunta se já está ativo
    i = parar.index("ollama ps 2>")
    antes = parar[:i]
    assert "systemctl --user is-active --quiet ollama-agata.service" in antes[antes.rindex("if command -v ollama"):]
    assert "systemctl --user stop agata.target" in parar  # socket, proxy e backend descem por aqui (PartOf)


def test_readme_documenta_a_migracao_sob_demanda():
    r = (SYSTEMD / "README.md").read_text(encoding="utf-8")
    assert "ollama-agata.socket" in r and "disable --now ollama.service" in r and "ln -sf" in r
    assert "ollama rm" not in r and "enable ollama-agata.service" not in r
