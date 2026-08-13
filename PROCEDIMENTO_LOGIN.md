# Procedimento — bug de login (senha recusada, espera de minutos, recusa de novo)

Escrito na sessão de MEMÓRIAS (124), depois de achar o mecanismo ao vivo no journal de
um episódio real (13/08/2026, madrugada). Não espere o bug reaparecer para ler isto.

## O que está confirmado por Máquina sobre a causa

Não é senha errada. É a máquina suspendendo e acordando sozinha em loop (s2idle,
`org_kde_powerde` pedindo suspend de novo a cada resume, ~91 ciclos numa noite) —
cada resume falha em recuperar o teclado USB de verdade (`usb ...: PM: failed to
resume async: error -5`, desconecta e reconecta com número de dispositivo novo) e
também a GPU (`NVRM: Failed to handle ACPI D-Notifier event`) e a EEPROM da RAM
(`spd5118 ...: PM: failed to resume async: error -6`) — sem que nenhum desses três
derrube o sistema. O efeito que chega à tela: teclas cortadas/perdidas durante a
digitação da senha (o teclado está reconectando bem no meio do processo de login) e
`pam_unix: conversation failed` repetido, que o `pam_faillock` acumula como falhas
reais até travar a conta ("Consecutive login failures... account temporarily locked").
Esperar não resolve porque o ciclo de suspend/resume não para sozinho — continua
gerando falhas novas durante toda a espera.

`unlock_time` do `pam_faillock` está no default, 600s (10 min) — perto dos "8 minutos"
relatados, não exato, mas na mesma ordem de grandeza.

## Passo a passo, na ordem

**1. Antes de mexer em qualquer coisa, `Ctrl+Alt+F2`** pra um TTY texto.
- Se o TTY aceita a senha: o problema é a pilha gráfica (`lightdm`/KDE), não a
  autenticação em si — volte pro `Ctrl+Alt+F1`(ou F7, a tela gráfica) e tente nela de
  novo, o TTY pode ter "destravado" o estado.
- Se o TTY também recusa: confirma que é `pam_faillock` (a trava é por conta, não por
  sessão gráfica) — vá pro passo 2.

**2. Se o TTY também recusar, tente `Ctrl+Alt+F2` de novo e rode, como root
   (`Ctrl+Alt+F1` pra tentar logar como root direto se tiver senha de root, ou via
   `sudo` se alguma sessão sua ainda estiver ativa em outro TTY):**
```sh
sudo faillock --user orusoua --reset
```
Isso limpa a trava sem esperar o `unlock_time`. Tente a senha de novo imediatamente
depois. **Pode falhar de novo se o ciclo de suspend/resume ainda estiver ativo** — não
é garantia, é o alvo mais certeiro que existe hoje.

**3. Se o reset de `faillock` não resolver (ciclo ainda ativo), o alvo é o ciclo, não
   a trava:**
```sh
sudo systemctl restart systemd-logind
sudo systemctl restart lightdm
```
(É `lightdm`, confirmado no journal desta máquina — não `sddm`, mesmo rodando KDE por
cima.) Isso não é garantido, mas se resolver, **confirma a hipótese por experimento**:
o problema estava no processo de sessão, não em disco/senha/hardware permanentemente
quebrado.

**4. Se nada dos acima resolver:** essa é a situação em que o desligamento forçado
segue sendo a única saída conhecida hoje. Antes de desligar, se der tempo, rode e
anote o resultado (não precisa salvar em arquivo, só olhar na tela):
```sh
journalctl -b 0 -u systemd-logind --no-pager | tail -30
journalctl -b 0 -k --no-pager | grep -i "failed to resume\|ACPI D-Notifier" | tail -10
faillock --user orusoua
```

## Sobre acesso remoto — achado importante, corrige PROJETO.md

`PROJETO.md` descreve acesso remoto "por Open WebUI sobre Tailscale". **Tailscale não
está instalado nesta máquina** — sem binário, sem serviço, sem interface de rede
(`tailscale0` ausente). SSH (`sshd`) está instalado mas **desabilitado e parado**.
Ou seja: hoje, se a tela travar, **não há como acessar a máquina de outro dispositivo**
— só o procedimento local acima. Corrigido no registro; decisão de reativar SSH/instalar
Tailscale é sua, não tomada aqui.

Se quiser um acesso mínimo de emergência sem reinstalar Tailscale agora, o mais rápido é:
```sh
sudo systemctl enable --now sshd
```
Isso expõe SSH na rede local (Wi-Fi de casa, `172.16.1.0/24` no momento deste
registro) — não é Tailscale, não é acesso remoto fora de casa, mas permite entrar de
outro aparelho na mesma rede pra rodar os passos 2-4 acima sem precisar tocar a
máquina fisicamente.
