---
name: agata-painel
description: Mexer no painel operacional do Agata (redesign/painel_operacional, porta 20146): alterar cores, textos, popups, rolagem, conversa com a Seth, rotas de API ou o estado da tela. Use antes de editar server.py, prototipo.js, prototipo.css ou prototipo.html, e antes de medir ou aplicar qualquer mudança visual.
---

# Painel operacional do Agata

Fatos medidos, não impressões. Antes de mudar qualquer coisa, leia a seção de regras; depois da mudança, meça na página real.

## Onde mora
- Código: `redesign/painel_operacional/` (`server.py`, `prototipo.html`, `prototipo.js`, `prototipo.css`, `test_painel.py`).
- Lista de conversas: mora no menu lateral (`aside.sidebar`, com Arquivadas, Lixeira, Organizar conversas e Serviços no rodapé), desde 16/11/2026. A seção Conversa tem só a tela da conversa; não repete a lista.
- Conhecimento: cinco blocos numa tela só, sem abas (âncoras `data-ancora` no topo). Não procure `data-sub` nessa seção.
- Telas de operação (17/11/2026): leituras `GET /api/equipe`, `/api/backup`, `/api/egress`, `/api/perimetro`, `/api/ci`, `/api/provedores` e `/api/qualidade-llm`; o painel não executa perímetro nem CI, só mostra o último resultado gravado.
- Herói do Panorama: sem retrato desde 16/11/2026 (o retrato fica só na marca da casca).
- Serviço: `painel-operacional.service` (usuário), porta **20146**, bind só em `127.0.0.1`. Depois de aplicar, reinicie: `systemctl --user restart painel-operacional.service`.
- Página: `http://127.0.0.1:20146/prototipo`. Só o `main` vale: o serviço serve o arquivo do checkout principal.

## Regras que o painel impõe (medidas)
- **CSP `style-src 'self'`**: `<style>` embutido e `style=` injetado por script são bloqueados em produção. Estilo entra em `prototipo.css`. Teste de estilo por injeção de `<style>` não é teste válido.
- **Nenhum link para fora**: nada de `obsidian://`, `target="_blank"` ou `href` externo. Vault vira tela própria, lida por `/api/vault/item` (lista fechada de 9 itens, ou `caminho=` restrito a `memoria/obsidian`, sem `..`).
- **Nenhum texto fixo que afirme estado** (contagens, "ativo", "Quatro…"). Estado vem da leitura do momento, com fonte e hora.
- **Setas `↗`** só em links que saem do painel. Botão que abre popup ou tela interna não leva seta.
- **Popup**: `dialog` com largura `min(680px, 100vw-32px)` e altura máxima `86vh`, cabeçalho e botões fixos, corpo com rolagem interna. Conteúdo longo rola dentro do popup; não corta.
- **Rolagem**: barras finas no tom da identidade (`scrollbar-width: thin` e `::-webkit-scrollbar`). Não esconda a rolagem de conteúdo que precisa ser lido.
- **Conversa com a Seth**: texto puro e Markdown montado com elementos do DOM. Nunca `innerHTML` com texto vindo da Seth.
- **Filtro de estilo (decisão do Humano, 16/11/2026)**: antes de entregar qualquer mudança de tela, leia `ESTILO.md` desta pasta (cópia do guia de estilo Agata, sem a seção final de registro) e aplique o checklist dele. Confira em 360, 768, 1440 e 2560 px, sem rolagem horizontal da página. Frase do Humano, 18:27: "esse estilo é o último filtro de requinte a partir de agora, estabeleça."

## Como medir antes de propor (método que funcionou)
1. **Pré-visualizar CSS sem tocar no arquivo**: busque o `prototipo.css` atual, transforme no navegador e aplique com folha construída (`new CSSStyleSheet(); sh.replaceSync(css); document.adoptedStyleSheets = [sh]`). Essa via não é bloqueada pela CSP. Confirme que as regras entraram (`getComputedStyle`).
2. **Contraste**: percorra cada nó com texto visível nas páginas, calcule luminância relativa (WCAG) do texto e do fundo mais próximo com cor opaca, e exija 4,5:1 para texto normal. Meça a contagem de textos e a dos que falham; registre as duas.
3. **Popups**: abra cada popup e meça `scrollHeight <= clientHeight` e `scrollWidth <= clientWidth` do `dialog`.
4. **Tela real**: depois de aplicar, meça de novo na página servida. Conte só o que o HTML servido tem (`curl` em `/prototipo`) e o que o navegador mostra.
5. **Navegador que aborta todo pedido que não é GET (medido em 16/11/2026)**: a medição de tela e de interação (abrir gaveta, abrir conversa, clicar em Mais) roda num navegador que aborta todo pedido que não é GET (no Playwright, `page.route`; no Chromium pelo protocolo CDP, `Fetch.failRequest`). Assim uma medição não escreve nada no painel. Registre quantos pedidos não-GET foram abortados (o número sai junto com a medição).

Números de contraste mudam entre medições por causa da quantidade de elementos visíveis. Registre sempre o total junto com o resultado.

## Como mudar (fluxo de proposta)
1. Trabalhe numa worktree (`git worktree add ... origin/main`), nunca no checkout principal.
2. Rode `python3 server.py --selftest` e `python3 -m unittest test_painel`. Se um teste antigo comparar formato exato, atualize a expectativa e diga isso.
3. Gere o `.diff` só com as alterações do painel (`git add -N` + `git diff origin/main -- redesign/painel_operacional`), confirme com `git apply --check`, e só então commite o `.diff` em `propostas/`.
4. O Humano assina. Aplique com `scripts/equipe/aplicar.py` e registro no formato DIÁRIO (ver `agata-aplicar-proposta`).
5. Depois da aplicação: reinicie o serviço, meça na página e registre o resultado.

## Armadilhas que já custaram tempo
- Caminhos com espaço (`~/Área de trabalho`) quebram `python3 -c` sem aspas: use argumento com aspas ou um script.
- `grep -o` com caracteres como `↗` pode falhar em alguns locais: use `python3` para contar.
- Matriz congelada, `pkill -f` e `git stash`: regras de `agata-equipe` e `agata-fluxo`.
- Playwright não estava instalado nesta máquina em 16/11/2026, e não se instala sem ordem do Humano. A medição de interação saiu pelo CDP do Chromium, com a biblioteca padrão do Python.

## Pendências conhecidas
- Medido em 16/11/2026 (deixa de ser pendência): fotos em oito larguras, de 360 a 2560 px (360, 480, 768, 1024, 1280, 1440, 1920 e 2560 px), com navegador sem janela e só GET, de panorama, conversa, conhecimento e sistema; e rolagem horizontal da página nas 64 combinações (8 larguras x 8 seções) pelo CDP, com 0 pedidos não-GET abertos. Resultado: nenhuma combinação com rolagem horizontal da página. Em celular, a gaveta e os mosaicos foram vistos em foto; o toque em alvo de 360 px não foi medido.
- O painel do Conselho (extensão e endpoint) está fora deste repositório, na área de trabalho. Ver `agata-fluxo` (memória comum) e `agata-equipe` (canal).

## Recomendação comprovada (L8)

Antes de recomendar uma solução para um erro desta skill, confira o desfecho registrado:

```bash
python3 redesign/router/skills_ledger.py recalcular --skill agata-painel
```

Procure a linha do erro e da solução na tabela (colunas: skill, erro, solução, usos, acertos, taxa, status). Recomende a solução como comprovada só com status `comprovada`: acertos acima de 51% e pelo menos 10 usos conferidos. Com status `não comprovada`, sem linha ou com código de saída 2, apresente a solução como "não comprovada", com os usos e a taxa quando houver, e não a descarte. Só conta o desfecho que o coordenador conferiu.
