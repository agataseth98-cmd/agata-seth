# Camada B — Bloco 3.2 (eco pós-carregar mecanizado) — briefing

**Para uma sessão de hidratação SEPARADA. Não pode ser a sessão que fez a Camada A**
(Claude Sonnet 5 na Máquina, 31/08/2026, commits `7a6b6cc`/`8588fab`). Um executor
em dois papéis anula a camada (REGRAS, "Cadeia de auditoria em camadas").

## Seu papel

Auditar a proposta da Camada A, levantar achados, e fechar com uma **posição**:
`APROVA` · `CONDICIONAL <o que falta>` · `REJEITA <por quê>`. Você **não** toca
canônico, **não** cria `APROVADO-`, **não** aplica o `.diff`. Sua saída é um
parecer que vai para a Camada C (que verifica suas alegações na Máquina) e para
o Humano.

## O que ler (fixado em commit — o repo é público)

Base: `github.com/agataseth98-cmd/agata-seth` @ `8588fab` (branch `main`).

1. `propostas/bloco-3.2-eco-mecanizado.diff` — a mudança. sha256
   `090c64e1b848caa2a3ba80535009bf45f5d5d6a1face6a5d750475aebe0ef4ae`.
   Toca `scripts/estado_para_eco.sh` (novo) + `REGRAS.md` (bullet "Eco pós-carregar").
2. `propostas/bloco-3.2-eco-mecanizado.md` — o registro da Camada A (Regra 8, testes).
3. `REGRAS.md` seção "Continuidade mecânica (TES)" e "Carregar e formatos"
   (`sync:` — três formas) — o contexto que a mudança encaixa.
4. `PROJETO.md` "Estado dos bugs e dos testes" — a linha TES-002 que o script cita.
5. Na Máquina (se você tem shell): `memoria/missoes/fase2-eco-camada-a/` —
   `prompt.txt`, `passada_{1,2,3}.txt` (saída crua das 3 passadas de Regra 8),
   `regra8-3-passadas.md`, `bateria-clone.md`. **Fora do repo público, sem remote**
   — se você é sessão de nuvem, não tem como ver; registre isso como `lacuna` e
   deixe para a Camada C.

## O que a proposta faz (resumo — confira contra o `.diff`, não contra isto)

- Script novo `scripts/estado_para_eco.sh`, read-only, determinístico. Imprime:
  `HEAD`, `TOPO-MEMÓRIAS` (1ª entrada após o marcador `ENTRADAS-NOVAS`), `SYNC`
  (PASS/FALHA/não-verificado contra `git ls-remote origin main`, formato do `sync:`
  de REGRAS), `PROPOSTAS-ABERTAS` (nº de `.diff` sem `APROVADO-`), linha TES-002,
  `HASH-ESTADO` (sha256 de HEAD+topo+hashes de REGRAS/MEMÓRIAS/PROJETO, 12 hex).
  Exit `0` utilizável · `1` SYNC FALHA · `2` marcador ausente.
- REGRAS "Eco pós-carregar": com shell, rodar o script e fundamentar o eco nele —
  **citar o `HASH-ESTADO` E dar 1 linha de por que o estado está coerente**; sem
  shell, declarar `sync: não verificado` e não preencher o que não mediu. O script
  imprime fatos, não escreve nem julga o eco — a conferência é do Humano.

## Decisões já tomadas (não reabra sem dado novo)

- **Regra 8, Q1** (só imprime vs. também valida o eco): convergiu — só imprime.
- **Regra 8, Q3** (obrigar vs. oferecer): convergiu — obrigar quando há shell.
- **Regra 8, Q2** (forma da prova anti-cópia): **decidida pelo Humano 31/08 —
  "hash + frase", mantém as duas.** Não é mais lacuna.

## Pontos que a Camada A entregou para você auditar

1. `HASH-ESTADO` colide conceitualmente com o nonce do TES-002? A proposta diz
   que não — derivado/público vs. secreto/`openssl`/nunca versionado. Confira o
   texto do script e da REGRAS: algum caminho em que um modelo trate o
   `HASH-ESTADO` como prova de continuidade (papel do nonce)?
2. "Obrigar só quando há shell" enfraquece o controle? A alternativa seria
   "sempre obrigar a *tentar* e declarar a falha". Avalie.
3. `SYNC: FALHA` sai com exit 1. Não há caller hoje (o modelo roda à mão).
   Confirme que a proposta não cria dependência oculta desse exit.
4. `grep -m1` do TES-002 casa `- **TES-002:**` literal no PROJETO.md. Se o PROJETO
   reformatar essa linha, o campo vira "(linha não encontrada)" — falha suave.
   Aceitável, ou precisa de âncora mais robusta?
5. Forme os seus próprios achados — os quatro acima não são a lista completa,
   são o que a Camada A já enxergou.

## O que você deve entregar (REGRAS, "O que cada camada deve entregar")

1. Verificação na Máquina antes de afirmar (hash, git, grep) — ou, sem Máquina,
   `lacuna` explícita em cada ponto que dependeria dela.
2. Citação exata do que citar, nunca paráfrase entre aspas.
3. Hedge sobre tudo que a Camada C não pode verificar a partir do seu texto.
4. Não tocar canônico. Autorização do Humano é pré-requisito de qualquer escrita.
5. Registro do que a Camada A **acertou**, não só do que errou.
6. (A confirmação pós-push é de outra etapa — não sua, mas saiba que existe.)

Assinatura: uma só, sua, no fim do parecer (`Modelo: … · vetor: … · turno: …`).
Não assine "pela Camada B" dentro de uma entrada de MEMÓRIAS — isso é da entrada
que registrar a aplicação, se ela acontecer.

## Onde sua saída vai

Um arquivo `propostas/bloco-3.2-camada-b-parecer.md` (quem tem Máquina comita;
sessão de nuvem entrega o texto e o Humano/executor comita). Sem `APROVADO-`.
Depois: Camada C na Máquina audita este parecer, e o Humano decide.
