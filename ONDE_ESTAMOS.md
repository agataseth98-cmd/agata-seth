# Onde estamos

## O que é isto
Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos. Teto: uma tela.
Histórico até 27/09/2026: `extras/arquivo/onde-estamos-ate-2026-09-27.md`.
O registro completo e permanente de tudo é `MEMÓRIAS.md` (entrada (599)).

## Onde estamos — 30/09/2026 (consolidado, pra retomar rápido se a sessão cortar)

**Fase 3 (instalar um Agata novo do zero) continua construída e aplicada de ponta a ponta** (estado de 27/09, sem mudança). **2 propostas novas esperando sua assinatura**, vindas da continuação do laboratório "Ensaio" (pasta `ensaio-2026-09-30/` na Área de trabalho):
- `propostas/portao-resume-exige-flag-2026-09-30.diff` — o comando que aprova uma mudança do grafo (`agata resume`) aprovava sozinho se você digitasse o "recusar" errado, ou não digitasse nada. Agora exige um dos dois, certo.
- `propostas/p4-llamacpp-portas-2026-09-30.diff` — 5 portas dos modelos locais (llama.cpp) não estavam na lista que o sistema confere; agora estão.
- Uma terceira sugestão do laboratório (restringir onde a Seth pode escrever) **não virou proposta** — a ideia partia de um engano sobre como a Seth escreve; registrado em `MEMÓRIAS.md` (599), nada mudou no sistema por causa dela.

**O que existe e funciona hoje, testado de verdade (não só escrito):**
- `bash scripts/genese.sh --framework <checkout> --destino <dir> --origin <url> --chave-publica <arq.pub> --nome <nome> --aplicar` nasce um clone completo — copia o framework, escreve o esqueleto, protege com sua chave desde o 1º commit.
- O teste automático (`testar_perimetro.sh`) funciona dentro desse clone novo (antes dava 8 erros, hoje 0).
- `~/agata` pode virar um atalho pra outro disco/pasta (`scripts/definir_caminho_agata.sh`), sem editar mais nada.
- `config/modelos-padrao.md` diz qual modelo de IA baixar primeiro, com o comando exato.
- `scripts/proteger_branch_github.sh` protege o repositório de um clone novo no GitHub — testado contra um repositório real, com um ataque real (push direto, recusado certo).
- `kokoro-tts` (que ninguém usava) saiu do sistema.
- O bug que faria um clone novo travar sozinho (`gerar_obsidian.py`) está corrigido.

**O que ainda falta, sem ser bloqueio pra usar o sistema hoje:**
- 2 arquivos de teste ainda esperam você apagar no seu Google Drive real (pasta "agata-sistema"): [`indice_export.md`](https://drive.google.com/file/d/1VAFCnnc3g-4yXEc5QKnb4Q_VwzRBLQ1n/view), [`manifesto.md`](https://drive.google.com/file/d/1zXNV5hUDyZ3XNAZp_UqyQQB5__LILDYP/view). Detalhe: `MEMÓRIAS.md` (579).
- Ninguém nasceu um clone de VERDADE ainda com `genese.sh` — só testes isolados, sempre apagados depois. A primeira vez pra valer ainda não aconteceu.
- As Fases 4 a 7 do plano de replicabilidade (memória em Obsidian como principal do clone; mecanismo de atualização a partir do oficial; onboarding assistido; teste de verdade ponta a ponta) não começaram.

**Se você está retomando depois de um corte de sessão:** confira `git log --oneline -5` e `gh pr list --state open` primeiro — nunca assuma que algo foi feito sem conferir. `MEMÓRIAS.md`, topo (marcador `ENTRADAS-NOVAS`), tem o relato técnico completo de cada passo, na ordem inversa (mais recente primeiro).
