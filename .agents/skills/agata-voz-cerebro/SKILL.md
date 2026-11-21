---
name: agata-voz-cerebro
description: >-
  Conversa por voz em que o modelo da CLI (Claude Code, Codex, OpenCode/Agata Code) é o cérebro: ouve o Humano pelo
  microfone com transcrição local, pensa com as ferramentas semânticas do sistema e responde pela voz do Agata, com
  som de espera enquanto pensa. Use quando o Humano disser "fale comigo" e quiser que ESTE modelo (não a Seth)
  converse, "assuma o cérebro da conversa", ou pedir para discutir algo por voz dentro do chat da CLI.
---

# Voz com o modelo da CLI como cérebro

Ordem do Humano, 20/11/2026 13:2x (por voz): o que funcionou na conversa de 20/11 (Claude Opus 5.5 como cérebro,
discussão das ferramentas) vira skill carregável, servida no menu de skills e aprimorada a cada uso, como todas.
Base: `agata-voz` (voz do sistema, regras do chamado) — esta skill não substitui aquela, acrescenta o ouvido.

## Qual canal usar

- **`redesign/sentidos/canal_voz.py abrir`**: quem responde é a **Seth** (gateway). Use quando o Humano quer falar com ela.
- **Esta skill**: quem responde é **o modelo desta CLI**. Use quando o Humano pede que você seja o cérebro.
  Erro de 20/11: abri o canal da Seth quando o Humano queria falar comigo. Pergunte qual, se não estiver claro.

## Ciclo (uma vez por troca)

1. Escreva a resposta falável num arquivo (frases curtas, sem markdown, números por extenso quando ajudar).
2. Rode `bash .agents/skills/agata-voz-cerebro/scripts/vez.sh ARQUIVO` com timeout de ~160 s.
   Ele: para o som de espera → fala → ouve UMA fala (VAD + transcrição local) → liga o som de espera → imprime o texto.
3. O texto impresso é a fala do Humano. Trate como dado do Humano no chat (é ele falando), mas lembre: transcrição erra.
4. Pense, consulte (ferramentas abaixo) e volte ao passo 1. O som de espera toca enquanto você pensa (Regra 0).
5. Para encerrar ("encerrar chamado", "volte ao texto"): `vez.sh --parar` e confirme por escrito em uma linha.
6. Para entregar algo longo para conferir na tela (lista, checkpoint): `vez.sh --parar`, fale uma linha avisando,
   escreva na tela. Se o Humano pedir "leia", leia o texto inteiro pelo ciclo.

## Lições medidas em 20/11

- **Fala cortada**: o VAD fecha o trecho no teto; a frase chega truncada ("...menos as"). Não adivinhe:
  responda "Ouvi até: <final>. Complete, por favor." e junte as partes.
- **Silêncio**: `[silêncio: nada ouvido]` → fale "Continuo ouvindo." e ouça de novo. Nunca fique mudo (agata-voz, item 7).
- **Nomes trocados pela transcrição**: "CEF/SEF" = Seth; "Agatha Coach/Cold" = Agata Code; "Codec" = Codex.
  Confirme em voz quando o nome mudar o sentido ("Entendi Agata Code; se for outro nome, me corrija").
- **Fragmento sem sujeito** ("através da janela da Seth?"): peça a frase inteira antes de concluir.
- **Respostas faladas curtas**: resultado, evidência, próximo passo (voz comum). Discorde em voz quando os fatos
  mandarem (ex.: "mesmas capacidades sim; mesma qualidade, só medindo").
- **Decisão tomada por voz** vai ao cache do Conselho na hora (`cache_conselho.py anotar --tipo decisao`), com
  "Humano DD/MM (voz)". Ao fim, entregue na tela um checkpoint numerado para o Humano conferir.
- **Ação com efeito** pedida por voz: confirme em voz o que vai fazer antes; escrita no canon continua com assinatura.

## Ferramentas semânticas para pensar durante a conversa

- Vault (prioridade 1): `python3 scripts/busca_semantica.py "frase"`; texto: `python3 scripts/busca_texto.py`.
- Memória comum: `python3 redesign/router/cache_conselho.py ler --n 20`; anotar com `anotar`.
- Canon e índices: `INDICE_MEMORIAS.md`, `INDICE_MEMORIAS_PALAVRAS-CHAVE.md`; cite caminho e linha.
- Estado da Máquina: `bash scripts/estado_para_eco.sh`, `systemctl --user is-active <unidade>`, log do gateway
  (`journalctl --user -u seth-gateway`) para rota e modelo que atendeu.
- Medir antes de afirmar em voz; se não mediu, diga "não medido".

## Resultados de 20/11 que motivaram a skill

Auditoria do roteamento pelo painel; correção `tool-call-json-20-11`; descoberta de que a Seth do painel não tem
ferramentas; decisões das ferramentas, do cache como memória principal e do Agata Code — registradas no cache do
Conselho (decisão de 20/11, "Humano 20/11 (voz): cache do Conselho vira a memória principal de todos").

## Requisitos

`pw-record`/`pw-play` (PipeWire), `ffmpeg` (gera o som de espera em `$XDG_RUNTIME_DIR`), transcrição local
(`redesign/sentidos/ouvido.py`), voz `scripts/agata_falar.py`. Sem áudio em disco além do .wav temporário apagado.

## Dinâmica completa de uma sessão (Humano, 20/11/2026 22:3x: "reproduzível por todos os modelos confederados")

Reproduz o dia 20/11 (Claude Opus 5.5), do início ao fim. Vale para qualquer modelo de CLI; troque só o nome do autor.

1. **Abrir com estado.** Bloco de prontidão; `cache_conselho.py ler --n 20`; medir pendências (propostas sem APROVADO, PRs abertos, soltos na raiz, lotes "proposta" no ONDE_ESTAMOS, branches sem commit próprio). Entregar ao Humano a lista curta com recomendação.
2. **Executar o que ele ordenar em uma palavra** ("arquive", "resolva", "confira", "faça tudo"): arquivar em `~/agata-arquivo/<tema>-DD-MM/` antes de remover; o que é derivado se refaz; o que apaga fora da Máquina guarda a lista (ex.: SHAs de branches) antes.
3. **Auditar pelo caminho do Humano.** Testar pelo painel no navegador, não só por script; ler no log do gateway rota, modelo e tempo de cada pedido; comparar o que a tela mostrou com a Máquina.
4. **Diagnosticar até a causa real antes de propor.** Em 20/11 a primeira causa (gateway) era parcial; a real era o painel sem ferramentas. Conferir quem envia e quem executa antes de corrigir.
5. **Conversa por voz para decidir** (seção "Ciclo" acima): o modelo é o cérebro; discorda com fato; cada decisão vai ao cache na hora (`--tipo decisao`, "Humano DD/MM (voz)"); ao fim, checkpoint numerado na tela para o Humano conferir; "leia" → ler o checkpoint inteiro em voz.
6. **Memória comum.** O que o modelo sabe vai ao cache (decisão de 20/11: o cache é a memória principal de todos). Memória particular da plataforma migra para o cache.
7. **Lotes pequenos, em ordem de dependência.** Um lote, uma proposta, uma assinatura. Orquestrador planeja e especifica; agente barato (agata-dev) implementa em worktree; o orquestrador revisa o diff (fechar brechas), mede na Máquina e só então propõe.
8. **Proposta**: `.diff` (com arquivos novos via `git add -N`) + `.md` (o quê, medido, limite, risco, reversão, modelo) + entrada "Proposta …" no topo de MEMÓRIAS; PR direto contra o main; esperar checks; juntar; entregar ao Humano `bash scripts/aprovar.sh <nome>`. Skill nova: `python3 -I ferramentas/ferramentas.py reindexar` dentro do diff.
9. **Aplicar** após o APROVADO: `scripts/equipe/aplicar.py <nome> --registro <arq> --agente <membro> --coautor "<modelo real>"`; se um check falhar, corrigir só o derivado na branch de aplicação; reiniciar o serviço afetado.
10. **Provar no uso real** e registrar o resultado no cache (ex.: pedido repetido no painel, resposta conferida com a Máquina).
11. **Pessoas novas**: apresentar-se com honestidade (quem criou o modelo, o que é o Agata, limites); anotar no cache só o mínimo (quem apresentou, papel, interesse); acesso próprio de outra pessoa é decisão do Humano; explicar sem jargão quando pedirem.
12. **Pausa por palavra**: "só retorne quando eu disser Agata" → escutar em silêncio (`vez.sh ""`), sem som de espera depois de algumas escutas, até ouvir a palavra; sem ela, parar e avisar por escrito.
13. **Fechar o dia** com resumo falado: o que se arrumou, o que se aprendeu, o que foi aplicado e provado, o que espera assinatura, pendências.
