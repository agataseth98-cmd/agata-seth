---
name: agata-mudanca-segura
description: Antes de mudar qualquer coisa que roda (unit systemd, container, firewall, config de serviço, rede, energia, boot) na Máquina. Portão das três perguntas + checagem de acoplamentos implícitos + prova pelo caminho real + como voltar.
---

# Mudança segura na Máquina

Por quê: o sistema quebra nas fronteiras que ele não modela (bússola T1, `extras/bussola/`). Em
24/09/2026 tirar UMA linha de uma unit consertou o Hyprland e, em silêncio, desligou a contenção de
suspensão e o fechamento do Obsidian (MEMÓRIAS (536)/(539)/(540)). Nenhum sensor pegou; só o teste real.

## 1. Portão das três perguntas (REGRAS, "Mudança estrutural") — responda por escrito ANTES
1. Desfaço sozinho, ou preciso de alguém? → escreva o comando de volta e faça o backup antes.
2. O que mais isto toca, além do que pretendo mudar? → seção 2, com comandos, não de cabeça.
3. Eu saberia se quebrasse? → qual comando/log mostra a quebra; se nenhum, a mudança precisa de um.

## 2. Acoplamentos implícitos — conferir com a Máquina
- systemd: `systemctl --user list-dependencies --reverse <unit|target>` e o inverso; quem tem
  `Wants/Requires/PartOf/BindsTo/WantedBy` apontando pra o que você muda (`grep -r` em
  `~/.config/systemd/user/` e `/etc/systemd/`). Target com `StopWhenUnneeded` para sozinho.
- Processo fora do cgroup: app Flatpak roda em `app-flatpak-*.scope` próprio (`PartOf=graphical-session.target`)
  — parar o serviço que o lançou NÃO o fecha.
- Portas: `config/portas-agata.txt` (P-4) e `ss -tlnH`; firewall: `ufw status numbered`.
- Serviços vigiados: lista do P-9 em PROJETO, "Serviços (boot)".
- Inibidores de energia/sessão: `systemd-inhibit --list`.
- Rode `bash scripts/perimetro.sh` antes e depois; diferença de veredito = acoplamento.

## 3. Prova pelo caminho real
- Não basta "o arquivo ficou certo": exercite o caminho que o Humano usa (botão, atalho `seth`/`seth-parar`,
  login, boot quando possível) e leia o log do instante (`journalctl --since`).
- Teste o lado negativo também (o que devia continuar bloqueado continua?).
- Evento que só se prova no próximo boot: diga isso e deixe como pendente com dono.

## 4. Registro
O que mudou fora do repo (runtime, `/etc`, `~/.config`) vai descrito na entrada de MEMÓRIAS com o
comando de desfazer. Efeito colateral achado depois é entrada nova, com "erro meu" dito sem suavizar.
