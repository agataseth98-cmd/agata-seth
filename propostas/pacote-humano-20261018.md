# Pacote do Humano — 18/10/2026

Tudo o que hoje depende **só de você**, numa lista. Sem nada do Codex. Fonte de cada item: `propostas/achados.md` (o ID AC-NN). Arquivo livre, sem `APROVADO-`; não autoriza nada por si.

Ordem: primeiro o que protege dado e acesso, depois as decisões rápidas, por fim as de desenho.

---

## A. Ações suas (precisam de você na Máquina)

### A1. Cofre: segunda cópia da chave e teste de restauração (AC-13)
- **Por quê:** a chave de recuperação só existe no pendrive NTFS marcado "sujo". Se ele falhar, o cofre não volta.
- **O que fazer:** (1) decidir onde fica a 2ª cópia (papel, outro pendrive ou os dois; `desenho-cofre-chaves-2026-10-16.md`, ponto 2); (2) rodar o teste de perda da máquina do mesmo documento: restaurar num diretório limpo só com a chave e a cópia cifrada. Precisa de `sudo`.
- **Recomendação:** papel + segundo pendrive, guardados em lugares diferentes.

### A2. Senha do LibreChat (AC-31)
- **Por quê:** nunca foi trocada desde 16/10 e não há como recuperá-la (sem e-mail de recuperação).
- **O que fazer:** não há tela para isso. No terminal, `docker exec -it librechat node config/reset-password.js` e digite o e-mail da conta. Depois, guarde a senha no seu gerenciador.

### A3. HD do backup (avisos P-6 e P-12)
- **Por quê:** a cópia fora da Máquina está parada (P-6: pendente desde ontem; P-12: cobertura conferida pela última vez em 21/09).
- **O que fazer:** conecte o HD `AgataBkup01` e siga `redesign/fase7-hd/QUANDO-O-HD-VOLTAR.md` (`restic snapshots`, `restic check`). Pode me pedir para conduzir os passos sem `sudo`.

### A4. Portas sem dono identificado (AC-12)
- **Por quê:** quatro portas abertas sem processo conhecido (42147, 44569, 5355, 631). Provável, **não medido**: 5355 = LLMNR do `systemd-resolved`; 631 = CUPS (impressão).
- **O que fazer:** rode e me mostre a saída:
  `sudo ss -tlnp | grep -E ':(42147|44569|5355|631)\b'`

### A5. Prova do boot (AC-43)
- Na próxima vez que a Máquina religar, nada a fazer: só me avise. Eu confiro se gateway, voz e LibreChat subiram sozinhos.

---

## B. Decisões rápidas (sim ou não)

### B1. Liberar a fila `rapido` com ferramenta (AC-01) — **recomendo: sim**
- **Estado (18/10, 15:45):** feito. Você disse sim; aplicado em MEMÓRIAS (774), gateway reiniciado, pedido simples com ferramenta já vai para `seth-rapido`.
- **Fato medido hoje:** 8 pedidos reais com ferramenta em cada fila, pelo gateway. `seth-rapido`: 7 chamadas corretas, 1 resposta em texto, 0 malformadas. `seth-livre`: o mesmo, 7/1/0. Latência mediana: rapido 0,85 s, livre 1,1 s. Ressalva: a `rapido` respondeu com `ministral-14b-latest` e a `livre` com `ministral-14b-latest` e `codestral-latest`; amostra pequena (8 + 8).
- **Hoje:** a trava manda para `livre` toda escolha `rapido` com ferramenta (95% das chamadas). Na prática a `rapido` está desligada.
- **Se sim:** eu preparo a proposta que tira a trava, com teste.

### B2. Tag `qwen3.5:9b` no Ollama (AC-11) — **recomendo: remover**
- **Fato:** o PROJETO proíbe usar a tag crua como principal; remover não libera os 6,6 GB (blobs compartilhados).
- **Se sim:** eu guardo antes a receita do Modelfile e confirmo que nenhuma rota a usa; o `ollama rm` é seu.

### B3. Consolidação que reprova sempre o mesmo tema (AC-09) — **recomendo: pular o tema depois de 3 reprovações**
- **Fato:** `reprovados.log` com 40 linhas; o juiz barra corretamente a citação errada, mas o mesmo tema volta todo dia e nada é gerado.
- **Opções:** pular depois de N reprovações (simples) ou corrigir o prompt do tema (mais trabalho, sem garantia).

### B4. Política do PROJETO cheio (AC-18) — **recomendo: aprovar**
- **Fato:** 47.979 B de 48.000. Proposta de regra: toda inclusão no PROJETO vem com uma retirada para `extras/projeto-detalhe/`.

---

## C. Decisões de desenho (pedem conversa)

### C1. Quem pode ver `moc-missoes.md` (AC-10)
- **Fato:** lista 3.404 caminhos privados e é alcançável por leitura direta e por busca textual.
- **Pergunta:** os nomes de caminho são públicos para a Seth e os modelos, ou ficam fora como a `segunda-camada`?

### C2. Canais (AC-15)
- **Fato:** decididos em 16/10 (Telegram, e-mail, Mastodon, Bluesky, Signal com aviso; fora WhatsApp e redes pagas), todos desligados; falta o contrato comum.
- **Pergunta:** qual canal primeiro? O cofre (F3 do AC-13) entra junto com ele.

---

## Fora deste pacote
- **Codex** (por sua ordem, 18/10): AC-06, AC-08 (K7), AC-22, AC-23, AC-24, AC-46, AC-48 a AC-53.
- **Comigo, sem depender de você:** AC-03 (interromper o treino do Laya sem estrago), AC-05/AC-07 (pesquisa e catálogo de modelos gratuitos), AC-16 (mutantes do fiscal), AC-20 (prova de campo do emoji), AC-38 (ampliar o golden).
- **Bússola, sem prazo:** AC-21, AC-25, AC-51.
