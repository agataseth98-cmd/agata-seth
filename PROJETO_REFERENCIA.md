# PROJETO_REFERENCIA.md — Seções de referência (não injetadas na hidratação)

Este arquivo contém seções de PROJETO.md que não são necessárias em toda sessão.
Disponível para consulta sob demanda (grep, leitura direta).

## VM do Marcos — nó de computação, não guardiã de canon
**Aceita 20/08/2026 (itens 4 e 7 do documento do Humano, MEMÓRIAS (223)).** O PROJETO já previa isto: "modelo local como classe é limitado neste hardware — o teto é ~14b/9GB. Assunto encerrado sem hardware novo." A VM oferecida pelo Marcos é exatamente essa condição chegando.

**Fronteira de confiança, decidida no papel antes de qualquer acesso existir** — mesma disciplina da quarentena P-8: a regra vem ANTES do mecanismo que ela vai restringir, não depois.

A VM é NÓ DE COMPUTAÇÃO. Nunca guardiã de canon.

- **VAI para lá:** o corpus congelado da bancada (`memoria/missoes/rlm-3caminhos/corpus` e `corpus_b0`), os runners (`rlm_c1.py`, `rlm_c1b.py` e variantes), os pesos dos modelos candidatos.
- **NÃO VAI:** nenhum `.env`, nenhuma chave, `memoria/missoes/` além do subconjunto explicitamente empacotado pro teste (nunca o diretório inteiro — `conselho-remoto/`, com backoff e pedidos, fica de fora), credencial de push, acesso de escrita a `origin/main`.
- **Resultado volta como arquivo de trace, e é DADO — mesma regra do Conselho Remoto acima.** Lido pelo Humano/executor antes de qualquer coisa acontecer com ele. Nunca executado, nunca interpretado como instrução.

**Por que registrar isto sem VM nenhuma ainda existir:** não há nada pra tecnicamente impor agora — sem acesso, sem risco concreto. O texto é o compromisso; quando a VM existir, o desenho de acesso (SSH, o que sobe, o que nunca sobe) tem que bater com o que está escrito aqui, não o contrário.

## Riscos conhecidos (limitações, não pendências)
- **Limite do princípio "ferramenta nova é decisão, não conserto" (228 - registrado com quatro provas, `scripts/ler_pagina.sh`).** Esgotar o que existe não é recusar o novo; o teste é se a ferramenta nova resolve uma classe que a atual não alcança.
- **Risco do `config.yaml`, fora do alcance da P-8.** `~/.hermes/config.yaml` guarda configuração de produção crítica, é editado por modelos e está fora do alcance da P-8 por morar fora do repositório. Já causou bug silencioso em (103)-(105 - teto de entrega do carregador truncando `.hermes.md` em silêncio). Mitigação atual é disciplina manual. Decisão pendente do Humano: criar mecanismo ou aceitar o risco declarado.
- **[FECHADO] P-7, checagem de citação, HABILITADO em `perimetro.sh` desde 17/08/2026.** `scripts/checar_citacao.sh`, testado positivo/negativo isolado e contra o corpus real. Checa só o que cada commit ACRESCENTA a MEMÓRIAS.md, nunca reaudita a história toda. Citação dentro de crases é exemplo de formato, pulada sem alarme (REGRAS, "Citação de MEMÓRIAS"); síntese composta com mais de um número no mesmo parêntese valida cada um. Limite conhecido, aceito por decisão do Humano: uma palavra genérica compartilhada pode deixar passar citação de assunto errado — generoso é a escolha certa, travar commit honesto é pior. Fecha a lacuna que a expedição RLM achou (fabricação por citação errada, não por entrada inexistente). MEMÓRIAS (203), (204).
- **[FECHADO] Saneamento de segurança em 5 passos, 15-16/08/2026.** Backup externo confirmado por restauração real, não listagem (188) · memória nativa do Hermes fora do rastreamento público, bypass de controle fechado (189, ver item próprio abaixo) · varredura de segredo ativa contra staged diff, 0 falso positivo em 20 commits reais (190) · diff do patch 429 versionado fora do vendorizado (190) · perímetro de 6 controles (`scripts/perimetro.sh`) amarrado ao `.githooks/pre-commit`, só depois de passar verde uma vez (191)/(192)/(193).
- O Gemini pode deixar de ser grátis. Plano B: pesquisar alternativas gratuitas quando doer.
- Silo é disciplina, não mecanismo, até a Fase 2.
- O patch do handler de 429 vive em repositório vendored sem backup — reverificar após todo `hermes update`.
- Desconfiança permanente tem custo. O overhead é campo opcional em MEMÓRIAS, sem automação; silêncio também é dado.
- Modelo local como classe é limitado neste hardware: o teto é ~14b/9GB. Assunto encerrado sem hardware novo.
- Fricções entre modelos de fornecedores diferentes são característica do período; registram-se quando surgem, não se resolvem por regra.
- **Sucessão do operador Humano é ponto único de falha.** O sistema trata sucessão de modelo com cuidado (Regra 6, silos, MOD), mas não tem plano pra sucessão do operador — só aparece em Fase 5, sem prazo. Se o Humano ficar indisponível, não há segundo operador definido.
- **Exposição do conteúdo do próprio DIÁRIO, não só do nonce.** A avaliação de risco do repositório público (MEMÓRIAS (62)/(70)) cobriu o nonce queimado, nunca o conteúdo do DIÁRIO coletivo em si — que já registra hábitos, hardware e rotina do Humano, e é público por decisão. Vale revisão futura sobre o que mover pra camada privada, sem editar história existente.
- **[FECHADO] Memória nativa do Hermes (`memoria/USER.md`, `memoria/MEMORY.md`) — exposição passada, decisão do Humano: NÃO FAZER NADA (17/08/2026, MEMÓRIAS (210)).** Escrita automática do mecanismo de memória do Hermes, nunca passou pelo controle de publicação deliberada — mesma classe de escrita fora de controle que apagou identidade em (47). Bypass de controle fechado 15/08/2026: `git rm --cached` + `.gitignore` (`memoria/*.md`, protege a classe). A exposição PASSADA (45 dias públicos, `dcdbc9c` a `ec99a0b`) fica como está, decisão consciente sustentada em quatro fatos: zero forks confirmados via API do GitHub — ninguém copiou o repositório no período; o conteúdo é dado pessoal do Humano, não credencial — não há o que rotacionar; a exposição futura já está fechada desde 15/08; reescrever história pra apagar é a linha vermelha da Regra 4, nunca esteve em discussão. MEMÓRIAS (189), (199), (210).
- **[PARCIAL] Cópia da história fora desta máquina — automática por commit, nos dois repositórios.** HD externo `AgataBkup01` (1,9T, exFAT); `post-commit` em `~/agata` desde 12/08 e, desde (160), espelhado em `memoria/missoes/` (prefixo `agata-missoes-*`), disparo verificado por restauração real. Veredito: **o gap está fechado, a dependência não.** Duas condições permanecem e não são teóricas: o HD **só grava quando fisicamente conectado** — sem ele, acumula marcador de pendência até alguém plugar; e a cobertura é **por commit, não por mudança de arquivo** — arquivo alterado e não commitado não gera bundle nenhum. **[FECHADO] `.env` fora do backup, decisão do Humano 17/08/2026 (MEMÓRIAS (205)).** Não entra cifrado nem cru — HD é exFAT, sem permissão de arquivo, segredo copiado pra lá fica legível por quem plugar o disco; chave se refaz em minutos, história não. `scripts/cifrar_env.sh` (GPG AES256, testado em S-3) segue existindo, mas não é mais o caminho recomendado. Se a máquina morrer, as chaves se refazem — risco assumido por escrito, não esquecimento. Histórico: MEMÓRIAS (116)/(117), (160), (205).
- **[FECHADO — EXPERIMENTO] "RLM em 3 caminhos" concluído 15/08/2026: 5 células (B0, C1, C1b, C4, C3), 240 respostas, UMA fabricação confirmada no experimento inteiro.** Portões do C3 confirmados ao vivo (184), C3 completo e determinístico em 3 rodadas (185), relatório final consolidando as 5 células (186), corrigido por ordem do Humano com denominador exato e decomposição honesta das falhas do C4 (187). A fabricação é de B0 (injeção total, sem ferramenta) — perguntada sobre a própria história, atribuiu com confiança um erro de (157) à entrada errada (143), idêntica nas 3 rodadas, verificada linha a linha contra o corpus; isto é sobre a arquitetura de PRODUÇÃO (injeção total no system prompt), não sobre um caminho experimental. C1/C1b (busca sob demanda, sem injeção total) não fabricaram nenhuma vez em 6 rodadas somadas. **Ocorrência confirmada, não taxa** — não se afirma frequência nem probabilidade a partir de uma amostra de um. **Em aberto, decisão do Humano, não decidida aqui:** qual caminho (se algum) vira produção — as leituras de (186)/(187) são PROPOSTAS do experimento, não veredito. Nada em produção mudou por este relatório; `qwen3.5-9b-64k` segue sob regime de auditoria como já estava. Histórico completo: MEMÓRIAS (163)-(187). **Análise pós-expedição (16/08/2026, MEMÓRIAS (195)):** trace diffing, custo por resposta certa e padrões de hesitação, sobre os mesmos traces — 5 leituras adicionais propostas, mesma regra de não decidir produção. Documento: `memoria/missoes/rlm-3caminhos/ANALISE_POS_EXPEDICAO.md`.
- **Alcance retroativo do bug de `grep -oE` achado em (105), não auditado.** O `grep` real desta máquina truncava matches de `-oE` com `[^\n]*`/similar em UTF-8 multibyte (português é acentuado; MEMÓRIAS inteiro é português). Não há como saber, sem auditoria manual, se alguma verificação de sessão anterior a (105) que tenha usado `grep -oE` sobre conteúdo acentuado produziu resultado incorreto registrado como confirmado. Não afirmado que algo caiu — registrado como possibilidade não descartada.

## ACB — bússola, não backlog
**Decidido em (223), 20/08/2026.** O ACB (14 fases, 17 adaptadores Workspace, ~30 serviços Google, 13 mensageiros, Discord, automação de navegador, 25 arquivos de documentação) não é backlog ativo — fica como referência de rumo. REGRAS "Contenção de escopo": só a fase atual e a seguinte têm gate e prazo; antecipar fase futura é negado por default, salvo ordem do Humano.

**Achado técnico, 20/08/2026 — muda o custo do nível L0 planejado (`browser.read`).** Ler HTML cru não enxerga a maioria dos sites modernos — o conteúdo é montado por JavaScript no navegador, não vem pronto no HTML. Verificado ao vivo contra `razionshefa.com.br`: HTML cru é casca vazia (5.778 bytes, sem texto real do site); o pacote JS referenciado (508.134 bytes, medido) continha o texto inteiro do site (título, descrição, seções — conferido linha a linha), extraído com dois `curl` e uma busca de string, sem instalar nada.

**Método, quando o texto está embutido no pacote (sites Vite/React estático — o caso testado):** `curl` da página → acha o `<script src=...js>` → `curl` do pacote → extrai as cadeias de texto longas. **Quando NÃO funciona:** conteúdo vindo de API em tempo de execução — o pacote só tem código, o texto chega depois por rede; aí é procurar a chamada de API dentro do pacote e ler a API direto. Se nem isso: `lacuna`, e usar navegador de verdade é DECISÃO do Humano, não conserto automático.

**Conclusão pro L0:** deixa de ser "baixar texto" (automático, sem risco, como o plano original descrevia) — passa a ter dois caminhos. O de dois `curl` (baixo risco, tentar primeiro) cobre parte dos casos. O de motor com JavaScript de verdade (Playwright, Puppeteer, Selenium, Chromium headless) traz superfície nova — **não instalado, não autorizado, não é pra agora.**

**Princípio geral, extraído deste caso, 20/08/2026:** "Antes de acrescentar ferramenta, esgote o que já se alcança com o que existe. Ferramenta nova é decisão, não conserto." Quatro ocorrências já registradas que o medem, não só o ilustram:
- (115) — `grep` venceu vector store/embedding em precisão, custo e auditabilidade nesta escala.
- a bancada congelada de (169) venceu construir uma suíte de testes nova pra seleção de modelo.
- `scripts/perimetro.sh` já era o "porteiro" pedido de fora como coisa a construir.
- dois `curl` (`scripts/ler_pagina.sh`, abaixo) venceram instalar navegador headless pra ler uma página montada por JavaScript.

**`scripts/ler_pagina.sh` — lê uma página sem navegador, só leitura.** Cinco casos em ordem: (1) texto no HTML cru, entrega e para; (2) casca vazia → acha o pacote `.js` referenciado, baixa, extrai as cadeias de texto longas; (3) pacote sem texto → procura a chamada de API dentro dele e reporta o endereço, **sem chamar**; (4) nada disso serve → `lacuna: conteúdo não está no HTML nem no pacote`. Sempre diz qual caso resolveu. Nunca relata "casca vazia" como "o site não tem conteúdo" — são coisas diferentes. Não envia formulário, não clica, não executa nada do que baixou.

**Testado antes de comitar:**
- **Positivo**, `razionshefa.com.br/pt`: HTML cru é casca vazia (18 caracteres de texto visível); pacote JS (508.134 bytes) continha o texto inteiro do site, em inglês e português, extraído e entregue como CASO 3.
- **Negativo**, fixture sintética local (HTML vazio + JS que só chama `fetch("/api/v2/conteudo")`, sem nenhum texto embutido): o script não inventou nada — achou e reportou o endereço `/api/v2/conteudo` como CASO 4, sem chamá-lo.

## Fronteira de recusas (propostas já decididas — não repropor)
Não é deliberação registrada aqui por hábito — é decisão. Sem esta tabela, cada modelo novo que lê um levantamento externo repropõe o que já foi recusado, com toda a razão de sua parte, porque o canon não carregava a objeção.

| Recusado | Motivo | Onde |
|---|---|---|
| Descarte de fatos por valor | Regra 4, absoluta | MEMÓRIAS (113) |
| Reconsolidação por reescrita | Já existe como entrada nova | MEMÓRIAS (113) |
| Reflections agendadas escrevendo memória | Mecanismo do bg-review, (47)/(48) | MEMÓRIAS (113) |
| Vector store como camada de memória | Refutado por medição nesta escala | MEMÓRIAS (115) |
| MEMÓRIAS em repo sem remote como cópia única | Privado também se versiona — git próprio, sem remote | (91)→(92) |
| RLM como auto-treino sem humano no loop | Regra 3 | MEMÓRIAS (114) |
| Conformidade com EU AI Act | Fora de escopo: pessoal, operador único, Brasil | — |
| Agent Reach (CLI multi-plataforma, github.com/Panniantong/agent-reach) | Não fecha lacuna que a Agata tenha (ler_pagina.sh já cobre a metade zero-config); antecipa fase do ACB sem ordem; soma risco de config fora do repo, já declarado e pendente | MEMÓRIAS (241) |
| Trocar o modelo principal por um candidato da bancada Frente 4 | Bancada de 6 fechada 21-22/08 na régua de (172)-(187): nenhum bateu o titular. `qwen3.5-9b-64k` 12/16 limpo, 0/16 fabricação; melhor candidato `gemma2:9b` 9/16 limpo, 1/16 fabricação. Só reabre com dado novo — release de modelo novo, OU falha medida do titular contra a mesma régua | MEMÓRIAS (234), (280); `RELATORIO_AVALIACAO_BANCADA_21-08-2026.md` |

## Diagnóstico
`hermes doctor` / `hermes status`. Prontidão da Agata: definida nas REGRAS.

