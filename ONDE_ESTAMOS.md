# Onde estamos

## O que é isto
Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos. Teto: uma tela.
Histórico até 27/09/2026: `extras/arquivo/onde-estamos-ate-2026-09-27.md`.
O registro completo e permanente de tudo é `MEMÓRIAS.md` (entrada (605)).

## Onde estamos — 30/09/2026 (consolidado, pra retomar rápido se a sessão cortar)

**Fase 3 (instalar um Agata novo do zero) continua construída e aplicada de ponta a ponta** (estado de 27/09, sem mudança). **As 3 propostas da continuação do laboratório "Ensaio" foram assinadas por você e já estão aplicadas de verdade nesta Máquina** — fila de assinatura pendente está zerada de novo:
- `agata resume` exige `--aprovar` ou `--recusar` — digitar "recusar" errado, ou não digitar nada, não aprova mais sozinho.
- As 5 portas dos modelos locais (llama.cpp) entraram na lista que o sistema confere.
- A Seth não consegue mais escrever em `scripts/`, `config/`, `REGRAS.md` e outros lugares sensíveis — reinstalei e reiniciei o serviço dela de verdade, testado ao vivo nos dois lados (continua escrevendo normal onde precisa; bloqueado onde não devia).

**Arquivo `propostas/modelos-gratuitos-2026-09-28.md` investigado e explicado** (era o "não rastreado" que a Seth não sabia identificar) — é pesquisa do "vigia de combustível", nada nele pede mudança agora. 2 modelos novos (`gemini-3-flash-preview`, `gemini-3.1-flash-lite`) apareceram funcionando fora do roster — decidir se entram é seu, quando quiser. Detalhe: `MEMÓRIAS.md` (600).

**`~/.config/agata/identificadores-pessoais.txt` criado**, com 3 identificadores já confirmados vazando no repositório (e-mail, IP e hostname do tailnet). O P-20 agora tem o que procurar. Se você tiver mais dado pessoal pra proteger (nome, CPF, telefone, endereço), me diga o valor e eu acrescento uma linha.

**Susto resolvido: o `omniroute` ficou fora do ar por ~1h40 hoje** (repositório do sistema atrasado, nada a ver com o Agata) — você rodou o `sudo pacman -S extra/simdjson` que eu pedi, confirmei que funcionou e reiniciei o serviço. Com ele de volta, entreguei a carta 2 do laboratório direto pra Seth (sem precisar você copiar e colar) — resposta dela auditada, sem problema desta vez. Detalhe: `MEMÓRIAS.md` (605), resposta completa em `ensaio-2026-09-30/harness-lab/resposta-carta2-seth-2026-09-30.md`.

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
