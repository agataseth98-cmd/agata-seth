---
name: agata-painel
description: Mexer no painel operacional do Agata (redesign/painel_operacional, porta 20146): alterar cores, textos, popups, rolagem, conversa com a Seth, rotas de API ou o estado da tela. Use antes de editar server.py, prototipo.js, prototipo.css ou prototipo.html, e antes de medir ou aplicar qualquer mudança visual.
---

# Painel operacional do Agata

Fatos medidos, não impressões. Antes de mudar qualquer coisa, leia a seção de regras; depois da mudança, meça na página real.

## Onde mora
- Código: `redesign/painel_operacional/` (`server.py`, `prototipo.html`, `prototipo.js`, `prototipo.css`, `test_painel.py`).
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

## Como medir antes de propor (método que funcionou)
1. **Pré-visualizar CSS sem tocar no arquivo**: busque o `prototipo.css` atual, transforme no navegador e aplique com folha construída (`new CSSStyleSheet(); sh.replaceSync(css); document.adoptedStyleSheets = [sh]`). Essa via não é bloqueada pela CSP. Confirme que as regras entraram (`getComputedStyle`).
2. **Contraste**: percorra cada nó com texto visível nas páginas, calcule luminância relativa (WCAG) do texto e do fundo mais próximo com cor opaca, e exija 4,5:1 para texto normal. Meça a contagem de textos e a dos que falham; registre as duas.
3. **Popups**: abra cada popup e meça `scrollHeight <= clientHeight` e `scrollWidth <= clientWidth` do `dialog`.
4. **Tela real**: depois de aplicar, meça de novo na página servida. Conte só o que o HTML servido tem (`curl` em `/prototipo`) e o que o navegador mostra.

Números de contraste mudam entre medições por causa da quantidade de elementos visíveis. Registre sempre o total junto com o resultado.

## Como mudar (fluxo de proposta)
1. Trabalhe numa worktree (`git worktree add ... origin/main`), nunca no checkout principal.
2. Rode `python3 server.py --selftest` e `python3 -m unittest test_painel`. Se um teste antigo comparar formato exato, atualize a expectativa e diga isso.
3. Gere o `.diff` só com as alterações do painel (`git add -N` + `git diff origin/main -- redesign/painel_operacional`), confirme com `git apply --check`, e só então commite o `.diff` em `propostas/`.
4. O Humano assina. Aplique com `scripts/dupla/aplicar.py` e registro no formato DIÁRIO (ver `agata-aplicar-proposta`).
5. Depois da aplicação: reinicie o serviço, meça na página e registre o resultado.

## Armadilhas que já custaram tempo
- `pkill -f` derrubou o shell e matou processos alheios: liste com `ps` e mate por PID.
- `git stash` é compartilhado entre worktrees: não use. Para guardar trabalho, faça commit WIP.
- Caminhos com espaço (`~/Área de trabalho`) quebram `python3 -c` sem aspas: use argumento com aspas ou um script.
- `grep -o` com caracteres como `↗` pode falhar em alguns locais: use `python3` para contar.
- `dupla.py aceitar-linha` altera a matriz congelada da sessão: é decisão do Humano, não do agente.

## Pendências conhecidas
- Layout em celular não foi medido (o navegador não redimensiona a aba).
- O painel do Conselho (extensão e endpoint) está fora deste repositório, na área de trabalho. Ver `agata-conselho-memoria`.
