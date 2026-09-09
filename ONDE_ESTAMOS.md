# Onde estamos

## O que é isto
Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos. Teto: uma tela.
Histórico até 08/09/2026: `extras/arquivo/onde-estamos-ate-2026-09-08.md`.
O registro completo e permanente de tudo é `MEMÓRIAS.md`.

## Onde estamos — 09/09/2026

**Duas consolidações fechadas** (395, 396): TES-002 nonce (já resolvido em
(90), só faltava o sinalizador) e OmniRoute 504 (causa raiz fora do nosso
controle, mitigação aplicada, proteção do pool grátis é mecanismo separado).
Nos dois rascunhos automáticos, boa parte das referências não tinha nada a
ver com o tema — descartei as erradas e documentei por quê. Backlog D2 anota
o bug do consolidador pra revisar depois.

**H3 do backlog fechado.** A Seth podia abrir com `Última entrada: (0)` quando
o pedido de estado (rede) demorava mais que 15s. Subi o timeout pra 25s e a
doutrina agora proíbe explicitamente inventar esse número — sem o bloco de
estado, ela escreve que faltou, não um número fabricado. Entrada 394.

## Onde estamos — 08/09/2026

**Aprovar mudança estrutural agora tem assinatura.** Você gerou uma chave
protegida por senha; a parte pública está no repositório. Pra aprovar uma
proposta você cola `bash scripts/aprovar.sh <nome> "motivo"` — ele assina,
e o perímetro só deixa o commit passar se a assinatura conferir. Eu não
tenho a senha, então não forjo aprovação. Trocar a lista de chaves também
exige assinatura (da chave atual). Entradas 365–367.

**Faxina feita.** Arquivei os lotes da "consolidação noturna" que nunca
deram nada, um experimento velho (spike RLM) e agora os documentos de
planejamento da era do Hermes (que foi removido em 03/09). Tirei do git
um log que sujava todo diff. Conferi arquivo por arquivo: tudo o que
está versionado tem função. Entradas 368, 372.

**Consolidação noturna consertada** (você escolheu consertar, não apagar):
só mexe num tema quando ele ganhou entradas novas; filtro mecânico joga
fora resumo vazio/errado antes de virar arquivo; usa o modelo local. O
robô continua **desligado** — religar: comando na entrada 371.

**Memória fria no Obsidian** deixou de aparecer solta: o mapa da memória
agora lista cada arquivo físico com a faixa de entradas que guarda.
Entradas 369, 370.

## O que falta (lista completa)

- **`redesign/` mistura código vivo com projeto fechado** — vale
  reorganizar. Preciso te apresentar uma proposta; é grande.
- **Rotação por família** (`propostas/dossie-rotacao-por-familia.md`) —
  desenho aberto, com perguntas pra você. Inclui se a Seth entra na
  rotação (hoje é papel fixo).
- **Duas costuras em REGRAS.md** (selo de hora com dois nomes; "última
  entrada" pedindo afirmação seca sob sync não verificado) — mexer em
  REGRAS exige segunda opinião de outro modelo.
- **TES-001 não fechado** — precisa de sessões de IA na nuvem
  genuinamente independentes; não dá pra fechar daqui.
- **TES-002** — reabrir com nonce novo depende de você entregar o nonce
  à mão a um modelo-alvo quando decidir.
- **`presence_penalty` na memória** — sob demanda: `consolidacao.py
  --temas "presence_penalty"` gera o resumo, você revisa e aprova.
- **Rotina de pesquisa de modelos gratuitos** (Proposta B) — job semanal
  que pesquisa, testa e escreve uma proposta; **implementação continua
  manual e assinada** (a Máquina não integra endpoint da web sozinha).
- **Âncora de frescor** (Proposta C) — ligar o carimbo de SHA que já
  existe no prompt de carregamento também no topo de REGRAS/PROJETO/
  MEMÓRIAS, pra um leitor offline saber se os três são do mesmo commit.

## Feito hoje que fecha esta rodada

- **Camada de proteção dos modelos externos** (entrada 374): quando um
  provedor grátis cai (aconteceu com os quatro no mesmo dia), o sistema
  agora se recupera sozinho — põe o provedor de castigo, rejeita resposta
  vazia ou truncada, tenta o próximo, e no fim cai no modelo local com
  aviso de que não é opinião externa de verdade. Um alarme novo (P-15)
  avisa se a camada externa está degradada. Investiguei a causa: são os
  provedores, não a nossa máquina nem a rede; a Seth (cérebro local) não
  é afetada.
- Backup do `memoria/missoes` gravado no HD. Timer da consolidação
  religado.
