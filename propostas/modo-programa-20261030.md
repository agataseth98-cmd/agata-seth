# Decreto: modo programa (29/10/2026 → 30/10/2026)

**O que muda:** ao ligar a Seth (atalho `seth`), o painel do Agata abre como programa, sem barra de endereço. O Obsidian não sobe mais sozinho. As janelas dos modelos e o LibreChat não abrem sozinhas: abrem quando você pedir pelo painel.

**Mudança:** só `redesign/systemd/seth`.
- Sai o início do Obsidian.
- O navegador abre com `--app` no painel (`/prototipo`), em vez de abrir painel e LibreChat como abas.
- Sai o bloco que abria as abas dos nove modelos.

**Limite de hoje:** sem os botões de abrir no painel (próximo Decreto), o LibreChat e os modelos ficam fechados até você abrir pelo navegador.

**Validado:** a sintaxe do `seth` passa (`bash -n`).

**Aplicação:** depois da assinatura (`bash scripts/aprovar.sh modo-programa-20261030 "aprovo: modo programa"`).
