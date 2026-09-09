# librechat-seth-iconurl — devolver o rosto da Seth no LibreChat

**Proposta P-8.** Par: `propostas/librechat-seth-iconurl.diff`.

## Porquê

A foto de perfil da Seth sumiu do LibreChat em 09/09/2026. Causa medida:

- A Seth era um **Agent** do LibreChat (`endpoint: agents`, `agent_id:
  agent_0Kdj6GbqpUe2rgKRIFmvk`) — a conversa "Learning Seth In My Language"
  (04/09) ainda usa esse binding. O avatar vivia no Agent.
- A migração pra **modelSpec** `seth-livre` (endpoint `Seth`, MEMÓRIAS (392),
  `enforce: true`) removeu o Agent. `db.agents` está vazio agora.
- modelSpec **não tem avatar** sem `iconURL` no `librechat.yaml`. Não havia
  nenhum. Resultado: ícone genérico de robô.

Nada foi perdido de verdade — só a referência. O PNG original (150×150, md5
`71870474a4a933ea83ce0a7cd5f63355`) foi recuperado de
`~/librechat/images/6a99c8514070d04134d59265/agent-agent_rHvH-6Q2lpcUyGMg7NaQp-avatar-1788955705933.png`
(idêntico ao de 04/09) e versionado em `redesign/librechat/assets/seth.png`.

## O que o `.diff` muda

`redesign/librechat/librechat.yaml`, só adições:

- `iconURL: "/images/seth.png"` nas 6 entradas de `modelSpecs.list` (com
  `enforce: true` a Seth aparece sempre via spec; é a spec que decide o rosto).
- `iconURL: "/images/seth.png"` no endpoint `custom → Seth` (fallback).
- 1 bloco de comentário explicando a origem.

Sem mudança de comportamento de roteamento, modelo, voz ou hidratação.

## Deploy (depois de `APROVADO-`)

1. Aplicar o `.diff` em `redesign/librechat/librechat.yaml` e mover o par
   `.diff` / `APROVADO-` pra `propostas/aplicadas/` no mesmo commit.
2. Copiar o asset pro runtime (fora do repo, bind-mount servido em `/images/`):
   ```
   cp redesign/librechat/assets/seth.png ~/librechat/images/seth.png
   ```
3. Copiar o yaml pro runtime:
   ```
   cp redesign/librechat/librechat.yaml ~/librechat/librechat.yaml
   ```
4. Reiniciar o container:
   ```
   docker restart librechat
   ```
5. Conferir na UI: nova conversa → Seth (cascata livre) → o rosto aparece no
   cabeçalho e no seletor de specs. Hard-refresh (Ctrl+Shift+R) se o navegador
   tiver cacheado o ícone velho.

## Alternativa descartada

Recriar a Seth como Agent (avatar nativo). Descartado: `enforce: true` nas
modelSpecs (MEMÓRIAS (392)) existe pra deixar só as 6 specs no seletor —
voltar pro Agent reabre o que (392) fechou.
