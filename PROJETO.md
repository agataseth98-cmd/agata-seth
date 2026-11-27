# PROJETO.md — Agata (índice)

Este arquivo é o índice: quem é o Agata, os princípios e onde está cada coisa. Não guarda estado nem história.
Estado vivo (portas, serviços, modelos, propostas, bugs): `ESTADO.md`, gerado pela Máquina por `scripts/gerar_estado.py`. Como operar: `PROTOCOLOS.md`. O que aconteceu, por número: `MEMÓRIAS.md`. Teto deste arquivo: 6.000 bytes; acima disso o pre-commit recusa o commit (`redesign/projeto_indice/teto.py`).
Se algo aqui contradisser MEMÓRIAS, MEMÓRIAS ganha: lá está o que aconteceu, aqui está o que vale hoje.
Se algo aqui contradisser a Máquina, a Máquina ganha — e a correção vira entrada nova em MEMÓRIAS.

<!-- ANCORA-SHA:INICIO (gerado por .githooks/pre-commit -- não editar as linhas abaixo à mão, o resto do arquivo é livre) -->
  SHA do commit ANTERIOR a este arquivo (limite conhecido: normalmente 1 commit atrasado; se o hook que grava esta linha falhar, pode ser mais -- ver a nota logo abaixo deste bloco, e PROJETO.md, "Memória e hidratação"): d1cccdc8022ec92152329f58bd2f25042ff73dcf
  Escrito em: 27/11/2026 15:07 -03
  URLs raw pinadas neste SHA (preferir estas -- imutáveis, sem risco de cache velho; mesma defasagem máxima do SHA acima):
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/d1cccdc8022ec92152329f58bd2f25042ff73dcf/REGRAS.md
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/d1cccdc8022ec92152329f58bd2f25042ff73dcf/PROTOCOLOS.md
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/d1cccdc8022ec92152329f58bd2f25042ff73dcf/FALHAS.md
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/d1cccdc8022ec92152329f58bd2f25042ff73dcf/PROJETO.md
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/d1cccdc8022ec92152329f58bd2f25042ff73dcf/MEMÓRIAS.md
<!-- ANCORA-SHA:FIM -->
<!-- Bloco de máquina (MEMÓRIAS (378)): SHA do commit anterior + URLs raw pinadas. Um leitor OFFLINE compara este SHA entre REGRAS.md, PROJETO.md e MEMÓRIAS.md -- se os três não baterem, a cópia é inconsistente (arquivos de commits diferentes). Numa interface que renderiza markdown estes comentários somem. Limite: normalmente 1 commit atrasado (auto-referência); mais se o hook falhar. -->


## O que é
Nome do sistema: Agata

Assistente pessoal do Orusoua, local-first e grátis por padrão.
Agata = **espinha determinística (git + `scripts/` + `perimetro.sh`)** + governança canônica
(REGRAS / PROTOCOLOS / FALHAS / PROJETO / MEMÓRIAS) + Conselho Federado de modelos.
- **Executor do loop:** grafo LangGraph + OmniRoute (redesenho mergeado na Fase 8, 03/09/2026 — (310)/(311)). Os modelos são trabalhadores substituíveis; nenhuma ferramenta É o sistema.

Grafia canônica do nome: **Agata** — sem acento, sem "h". A história migrada usa grafias antigas; não se corrige história.

## Princípios
Adotada pelo Humano, 17/08/2026 (201). Ferramenta de decisão situacional do Humano (Regra 3), não regra universal:
- Incidente é o que passa ao lado de um controle que o sistema declarou. O resto é risco de fundo: registra e segue.
- Defesa só entra se for mecânica e no limite. Vigilância humana permanente decai; mecanismo instalado não.
- Risco residual declarado é mais seguro que estado "seguro" não declarado.
- Fecha a classe, não o caso.
- Nenhuma checagem entra em hook antes de passar verde uma vez.

## Onde encontrar

Cada caminho da coluna "Onde está" existe; o teste `OndeTests` confere. Para estado vivo, leia `ESTADO.md` antes de qualquer tabela.

| Pergunta | Onde está | Como consultar |
|---|---|---|
| Portas, serviços declarados, modelos que responderam, propostas, bugs abertos | `ESTADO.md` (gerado) | `python3 scripts/gerar_estado.py` |
| Serviços declarados (fonte do P-9 e do painel) | `config/servicos-agata.txt` | uma linha por unidade |
| Portas e bind esperado | `config/portas-agata.txt` | P-4 confere o bind real |
| Modelos e filas | `config/modelos-gratuitos.md` | seção "Confirmado funcionando" |
| Máquinas, cérebro, interface, prosa de estado, plano vigente, bugs | `extras/projeto-detalhe/estado-de-fundo-12-11.md` | sob demanda |
| Regras: o porquê | `REGRAS.md` | |
| Como operar: P-8, sudo, hidratação, Conselho, decisor, voz, personalidade, memória | `PROTOCOLOS.md` | `python3 scripts/busca_texto.py "termo"` |
| Memória e hidratação (silos, janela, âncora) | `PROTOCOLOS.md`, "Memória e hidratação" | |
| Falhas por causa raiz | `FALHAS.md` | |
| Histórico de decisões, por número | `MEMÓRIAS.md` e `INDICE_MEMORIAS.md` | `python3 scripts/busca_texto.py "termo"` |
| O que o Humano lê hoje | `ONDE_ESTAMOS.md` | |
| PROJETO.md anterior, byte a byte | `extras/arquivo/projeto-ate-2026-11-12.md` | sha256 em `redesign/projeto_indice/destinos.json` |
| Destino de cada seção que saiu daqui | `redesign/projeto_indice/destinos.json` | `python3 redesign/projeto_indice/verificar_destinos.py` |
| Propostas P-8 | `propostas/README.md` | `ls propostas/` |
| Fronteira de recusas, VM do Marcos, riscos, ACB | `PROJETO_REFERENCIA.md` | |

## Referência
Seções de consulta (VM do Marcos, riscos conhecidos, ACB, fronteira de recusas, diagnóstico) estão em `PROJETO_REFERENCIA.md` — não injetadas na hidratação, disponíveis sob demanda.

