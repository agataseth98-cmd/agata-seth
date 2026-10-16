# Desenho G-C: cofre de chaves da Agata (16/10/2026) — SÓ DESENHO, sem código

**Estado:** proposta de desenho para o Humano aprovar. Nada aqui está implementado. Autor: Claude Code (assumindo o C12 do Codex, que volta às 18:35 para revisar). Origem: Decisão 8 do Humano (15/10/2026): "solução nossa, à prova de falhas, com ciclos de atualizações aos padrões do mercado", confirmada como **camada da Agata sobre primitivas padrão já auditadas, sem criptografia escrita por nós**. Pré-requisito de qualquer canal que use chave (Telegram, e-mail, Mastodon, Bluesky, Signal), decidido em 16/10.

## 1. O que existe hoje (medido em 16/10/2026)
- Segredos em ~9 lugares (`CHAVES.md`): `~/.config/agata/.env` (chaves de API dos provedores, token do Discord), `restic.pass`, `obsidian.token`, `google-project/`, `token-interno`, `~/.omniroute/.env`, `~/librechat/.env`, `PRIMEIRO-ACESSO.txt`. Permissão 600; nada no git.
- **Cópia de recuperação já existe, mas está velha:** `scripts/cifrar_env.sh` cifra o `.env` com GPG simétrico (AES256) e grava `env-AAAAMMDD.gpg` no staging e no restic. A última cópia é de **03/09/2026**; o `.env` foi alterado em **22/09/2026**. A cópia **não contém** as mudanças dos últimos 19 dias, e nada avisa.
- Ferramentas na máquina: `gpg`, `ssh-keygen`, `systemd-creds` (systemd 262). **Ausentes:** `sops`, `age`.
- Não existe: inventário de segredos com validade, ciclo de rotação, aviso de vencimento, teste de restauração.

## 2. Ameaças que o desenho cobre (e as que não cobre)
Cobre: perda da máquina ou do disco; segredo vazando em log, chat, commit ou saída de modelo; chave esquecida por meses sem rotação; cópia de recuperação desatualizada; um canal novo ganhando acesso a segredo que não é dele.
**Não cobre:** processo malicioso rodando como o mesmo usuário com a máquina desbloqueada; comprometimento do próprio provedor; perda simultânea da máquina e do segredo-mestre.

## 3. Desenho em 3 camadas (cada uma com primitiva padrão)
1. **Manifesto de segredos (a camada da Agata).** Um arquivo versionado `config/segredos-manifesto.txt` com **só nomes e metadados, nunca valores**: nome, onde mora, quem usa (serviço), classe (A: chave de provedor pago/limite; B: token de canal; C: criptográfica interna), prazo de validade em dias, última rotação, como rotacionar (ponteiro para `CHAVES.md`). É a única parte escrita por nós.
2. **Entrega ao serviço: `systemd-creds`** (já instalado). Cada serviço recebe o segredo por `LoadCredentialEncrypted=`, cifrado e amarrado à máquina (TPM2 quando houver; senão a chave do host). O serviço lê em `$CREDENTIALS_DIRECTORY`, sem variável de ambiente nem arquivo legível por outros. Migração **por serviço**, um de cada vez, começando pelos canais novos.
3. **Recuperação portátil: GPG (já em uso)** em vez de acrescentar `sops`+`age` agora. Mantém `cifrar_env.sh`, mas passa a cifrar **o conjunto declarado no manifesto** (não só o `.env`) para **uma chave pública do Humano**, de modo que a cópia possa ser feita automaticamente sem a senha; a chave privada fica **fora da máquina** (papel ou pendrive). `sops`+`age` ficam como evolução opcional (Decisão 2: instalação assistida, `sudo` do Humano), se a edição de segredo versionável valer o software novo.

## 4. Ciclo de vida
- **Verificação diária (só leitura, nunca abre valor):** `scripts/verificar_cofre.py` compara o manifesto com o disco. Avisa (não bloqueia): segredo sem entrada no manifesto; entrada sem arquivo; permissão diferente de 600; **cópia de recuperação mais velha que o segredo**; segredo vencendo em 14 dias ou vencido.
- **Rotação por classe:** A (provedor) a cada 180 dias ou ao primeiro sinal de vazamento; B (canal) a cada 90 dias; C (interna) só por evento. A rotação é **ato do Humano** (`CHAVES.md` passo a passo); a máquina só avisa e, depois, atualiza o manifesto e refaz a cópia.
- **Revisão do próprio desenho** a cada 6 meses contra o padrão de mercado (OWASP Secrets Management, documentação do systemd): fonte a conferir no momento.

## 5. Provas exigidas antes de dar o cofre por pronto
1. Teste de **perda da máquina**: restaurar de zero numa VM ou diretório limpo, só com a chave privada fora da máquina e a cópia cifrada; o serviço sobe.
2. Teste de **vazamento**: segredo sintético colocado em log, chat e saída de modelo é barrado pela varredura existente (P-1 e o sanitizador) — sem usar segredo real.
3. Teste de **falha fechada**: serviço sem credencial não sobe com segredo vazio nem cai em padrão inseguro.
4. A cópia de recuperação **sempre** mais nova que o segredo (aviso do item 4).

## 6. Fases (menor passo primeiro)
- **F1 (sem risco):** manifesto + `verificar_cofre.py` só de leitura + aviso de cópia velha. Já corrige o achado dos 19 dias. Proposta P-8 pequena.
- **F2:** `cifrar_env.sh` com chave pública do Humano e conjunto do manifesto; teste de restauração.
- **F3:** `systemd-creds` para o primeiro canal novo; os existentes migram um por vez, só com ensaio.
- **F4 (opcional):** `sops`+`age`.

## 7. O que o Humano decide
1. Aprovar este desenho (F1 a F3) e a ordem.
2. **Onde guardar a chave privada de recuperação** (papel, pendrive, ou ambos) — decisão só sua, a máquina não escolhe.
3. Aceitar GPG agora e deixar `sops`+`age` para depois (menos software novo), ou instalar `age` já.

## 8. Fontes e limites
Estado da máquina: medido hoje (`command -v`, `stat`, `scripts/cifrar_env.sh`, `CHAVES.md`). Práticas de mercado (OWASP Secrets Management Cheat Sheet; `systemd.io/CREDENTIALS`): citadas da pesquisa de 15/10/2026 no plano, **lidas só em trechos**; reconferir na fonte antes de implementar. Não verifiquei se há TPM2 nesta máquina (`lacuna`).
