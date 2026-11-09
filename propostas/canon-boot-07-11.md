# Proposta: PROJETO.md sobre o que sobe no boot (07/11/2026)

## Em uma frase

Corrige o PROJETO.md em três pontos: `agata.target` está sob demanda (decisão de 29/10/2026); `ollama.service` fica fora do boot (decisão do Humano de 07/11/2026); o LibreChat está em substituição pelo chat do painel, com os contêineres em `restart=no` desde 07/11/2026.

## O que muda

`PROJETO.md` (9 trechos):

1. **Frentes** (linha 37): LibreChat marcado "em substituição pelo chat do painel", sai do sistema depois da entrega medida.
2. **Acesso remoto** (linha 38): "LibreChat (em substituição, ver Frentes)".
3. **Máquinas › Predator › Boot** (linha 44): frase nova "Fora do boot": `agata.target` (sob demanda desde 29/10/2026) e `ollama.service` (desde 07/11/2026). Fica fora da seção "Serviços (boot)" de propósito, porque o painel lê essa seção e cobraria a unidade quando ela estiver parada por decisão.
4. **Serviços (boot), `agata.target`** (linha 68): "habilitado no boot" vira "sob demanda desde 29/10/2026: não sobe no boot; o atalho `seth` liga, `Parar Seth` desliga".
5. **Serviços (boot), rótulo** (linha 75): "Gateway e voz no boot" vira "Gateway e voz sobem com o `agata.target` (sob demanda, não no boot)".
6. **Serviços (boot), stack do LibreChat** (linha 80): "`restart: unless-stopped` em tudo" vira "`restart: no` desde 07/11/2026 (medido com `docker inspect`: 4 contêineres, rodando); antes era `unless-stopped` em tudo", mais "em substituição" e a pendência de a fonte `redesign/librechat/docker-compose.yml` ainda dizer `unless-stopped`. A descrição de como funciona hoje segue.
7. **Serviços (boot), "Também no boot"** (linha 83): sai `ollama.service (sistema, :11434)`. `agata-manutencao.timer` e `agata-vault-inbox.timer` seguem como estavam.
8. **Interface, LibreChat** (linha 111): "Em substituição pelo chat do painel (decisão do Humano, 07/11/2026): sai do sistema depois da entrega medida; a descrição abaixo segue valendo até lá."
9. **Interface, Atalhos** (linha 116): "Parar Seth (para as frentes; `agata.target` segue de pé)" vira "(para as frentes e o `agata.target`, e libera a VRAM)". Motivo: `redesign/systemd/seth-parar` faz `systemctl --user stop agata.target` (linha 34), e a frase antiga contradizia o código.

`scripts/perimetro.sh` (1 trecho):

- `P9_UNIDADES_SISTEMA=("ollama.service")` vira `P9_UNIDADES_SISTEMA=()`, com comentário de 3 linhas. Motivo: com a lista antiga, o P-9 avisa hoje `unidade de sistema 'ollama.service' está 'disabled'` (medido). A lista segue a linha "Também no boot" do PROJETO, que deixou de citar o Ollama.
- Efeito: o P-9 deixa de conferir se o Ollama está no ar. `_p9_ollama_na_gpu` (modelo dividido entre GPU e CPU) continua.

## Fonte de cada decisão

- **agata.target sob demanda:** `propostas/aplicadas/APROVADO-sistema-sob-demanda-20261029` (aprovado pelo Humano em 29/10/2026, 15:29 -0300, motivo "aprovo: sistema liga e desliga pelos atalhos") e `propostas/sistema-sob-demanda-20261029.md`, seção "O que não muda": "Nada do sistema sobe sozinho ao ligar o computador". O código confirma o atalho: `redesign/systemd/seth` inicia o `agata.target` (linha 13) e `seth-parar` o para (linha 34). Medido em 07/11/2026: `agata.target` `disabled` e `inactive`.
- **ollama.service fora do boot:** decisão do Humano em 07/11/2026 (resposta "não" à pergunta "Ollama sobe no boot?"). Não há registro escrito dela no repositório (busca em `propostas/` sem resultado para 07/11). Medido em 07/11/2026: `ollama.service` `disabled` e `active`. Os atalhos não o ligam nem o param: `seth` não cita o Ollama, e `seth-parar` só descarrega os modelos (`ollama stop`).
- **LibreChat em substituição e restart=no:** decisão do Humano em 07/11/2026. Também não há registro escrito no repositório. Medido em 07/11/2026 com `docker inspect`: `librechat`, `librechat-ponte-host`, `librechat-mongodb` e `librechat-meilisearch` com `restart=no` e `running`.

Assinar esta proposta é a confirmação formal das duas decisões de 07/11/2026.

## O que não mudou e por quê

- **`agata-manutencao.timer` e `agata-vault-inbox.timer`** seguem em "Também no boot": sem decisão do Humano sobre eles. Conflitam com "Nada do sistema sobe sozinho ao ligar o computador" (29/10/2026). Fica para decisão.
- **Título "## Serviços (boot)"** mantido: o painel (`redesign/painel_operacional/server.py`, lacunas) e o cabeçalho do P-9 (`scripts/perimetro.sh`) buscam esse texto. Renomear quebraria os dois.
- **`redesign/librechat/docker-compose.yml`** ainda tem `restart: unless-stopped` (linhas 32, 42, 55 e 80). Está fora desta proposta. Sem alinhar a fonte, recriar um contêiner pelo compose volta a `unless-stopped`.
- **Descrição de como o LibreChat funciona hoje** (Stack, Interface, Predator, portas da linha 139, discord/navegador da linha 117): mantida, por instrução. Continua correta até a remoção.
- **Linhas 76 e 81** ("habilitado no `agata.target`"): não editadas. Medido: `seth-gateway.service` e `piper-tts.service` aparecem `disabled` em `systemctl --user is-enabled`, então a frase pode estar defasada. Não verificado a fundo.
- **Trava "sistema desligado" para unidade de sistema:** `scripts/perimetro/p09_servicos_declarados.sh` tem essa trava só para unidades de usuário. Com o Ollama fora da lista, o P-9 deixa de avisar a queda dele com o sistema ligado. Se o Humano quiser esse aviso, é mudança de lógica (não de lista) e fica para outra proposta.
- **Derivados e cópias:** `extras/projeto-detalhe/servicos-e-interface.md` (linha 7) ainda lista `ollama.service` no P-9; `scripts/perimetro-sombra-referencia.sh` (linha 1044) ainda tem a lista antiga; `redesign/painel_operacional/server.py` (linha 623) tem docstring citando o Ollama como "declarado no boot". Não editados. A referência não muda o código de saída do P-9, porque o P-9 só avisa.

## Verificação

- CI local (`PYTEST=... bash scripts/ci_sdd_local.sh`, com as edições): `CI LOCAL: TUDO OK`, 33 passos OK, 0 FALHA.
- `scripts/testar_p9.sh`: `P-9: OK`.
- `scripts/testar_cobertura_servicos.py`: `COBERTURA SERVICOS OK -- 11/11`.
- P-9 com o systemd vivo (somente leitura): com a lista antiga, aviso `ollama.service 'disabled'`; com a lista nova, nenhum aviso sobre o Ollama.
- `git apply --cached --check` do diff contra a base: OK.
- Não rodado: `scripts/testar_perimetro.sh`. A suíte comita em clones de teste, e a regra desta sessão proíbe `git commit`. O workflow `perimetro.yml` a roda no CI.

## Como o PR entra

O PR desta proposta contém só `propostas/canon-boot-07-11.diff` e este registro. As edições de canon ficam fora do commit: sem o par assinado, o P-8 e a guarda de âncora do `pre-commit` barram a mudança de `PROJETO.md` e de `scripts/perimetro.sh`.

## sha256 do diff

`d7fb1c15581c8e8c2de189c245b498f68dbe662474974fce19760f0e6d912237` (`propostas/canon-boot-07-11.diff`, 15098 bytes)

## Aplicação

Depois da assinatura do Humano (`bash scripts/aprovar.sh canon-boot-07-11`), aplica-se o diff no main com `git apply propostas/canon-boot-07-11.diff`, e o par `.diff`/`APROVADO-canon-boot-07-11` vai para `propostas/aplicadas/` no mesmo commit (`propostas/README.md`, passo 4).
