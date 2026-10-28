# Onde estamos

Atualizado em 28/10/2026.

Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos. Teto: uma tela.
Histórico até 22/10/2026: `extras/arquivo/onde-estamos-ate-2026-10-22.md`.
O registro completo e permanente de tudo é `MEMÓRIAS.md`.

## Hoje, 28/10

**Aplicação da Equipe, 28/10:** assinatura verificada; a aplicação está preparada em PR e aguarda o merge humano. Após o merge: atualizar `agata-vigia@.service`, recarregar o systemd do usuário e provar as unidades de Claude e Codex.


**Esperando a sua assinatura:**
- `aplicar-refazer-base-20261028`: quando o main anda antes do merge, o script de aplicação refaz o PR sobre o main novo, em vez de misturar os dois e travar em conflito. Depois dele, o Discord pode ser reaplicado.
- `equipe-universal-20261028`: a dupla passa a se chamar Equipe e aceita qualquer membro do Conselho, não só Claude e Codex. Assine depois da anterior: as duas mexem no mesmo script.

**Aplicado no PR #674:**
- RelayCouncil: contrato v3 e catálogo de 17 provedores, com entrada por API oficial ou manual. Automação do navegador fica fora.
- O painel e os serviços em execução não foram alterados.

**Aplicação P-8 do endpoint local, em revisão:**
- A assinatura foi validada e o endpoint de catálogo e registro entrou na branch de aplicação. O PR aguarda revisão e merge humano.
- A interface RelayCouncil e a conexão com provedores ainda ficam para etapas posteriores. Os serviços em execução não foram alterados.

## Hoje, 22 e 23/10

**Já valendo (assinado e aplicado):**
- A Seth responde pela cascata com a memória completa. Dados pessoais deixaram de bloquear a saída externa; só segredo continua bloqueado.
- A escrita em MEMÓRIAS pelo LibreChat exige sua aprovação, e foi comprovada uma vez. O diário saiu do chat.
- O escriba exige token por projeto e recusa segredo antes de gravar.
- O migrador de história e o gerador do mapa do PROJETO entraram (pacote 2a).
- O mapa do PROJETO na hidratação (pacote 2b). Medido em cópia: a hidratação caiu de 124 mil para 88 mil caracteres.
- A suíte de testes roda em paralelo, até 4 casos ao mesmo tempo. Antes levava cerca de 205 segundos; agora, cerca de 56 segundos, medido duas vezes com os 58 casos passando.

**Esperando você:**
- Assinar as propostas em conjunto, quando estiverem prontas. Hoje, uma: a correção da entrada 817 do MEMÓRIAS.
- Lista de nomes de projeto: não é necessária para a Seth funcionar. Só faz sentido se houver nome que não deva sair para a nuvem.

**Com o Codex:**
- As pastas reports, research_notes e o arquivo sh são do Codex. Serão sanitizadas quando o trabalho dele estiver concluído. Até lá, não são movidas.
- Propostas antigas: cinco não se aplicam mais ao main e não serão assinadas. Uma (cabecalho-modelo-real) ainda se aplica e será conferida antes de qualquer assinatura.

**Em espera:**
- Backfill das 11 tags dos chunks frios: depois de 29/10.
- Roteamento por capacidade: próxima frente, depois da correção da 817.

**Fechado:**
- Sombra em segundo plano (PR 474).
