# redesign/router/ — camada do gateway de modelo (Fase 1)

**Não é canon.** Branch `redesign`. Suporte à Fase 1 (OmniRoute como gateway único).

## `sanitizar.py` — scrub de segredo antes do egresso (P1-02)

Feito 2026-09-01 ("continuar sem o HD"), **testado offline**, ainda **não ligado** ao
caminho de saída (isso é o passo 3 da P1-02, quando o OmniRoute estiver de pé).

### Régua única

Os padrões vêm de `scripts/varredura_segredo.sh` (`PADROES_SEGREDO`, 7 regexes ERE),
extraídos em runtime por `bash -c 'source ...; printf "%s\n" "${PADROES_SEGREDO[@]}"'` —
**sem segunda cópia**, sem re-digitar. Se o `.sh` mudar a régua, o `--autoteste` acusa.

Única tradução ERE→Python: `[[:space:]]` → `[ \t\n\r\f\v]` (semântica C-locale). Qualquer
outra classe POSIX (`[[:alnum:]]` etc.) faz `PadraoNaoTraduzivel` — o módulo **não
adivinha**.

### Contrato

- `varrer(texto) -> [{padrao_rotulo, padrao, trecho_redigido, pos}]` — `trecho_redigido` é
  `<4 chars>…[N chars]`, **nunca** o valor.
- `sanitizar_payload(payload: dict) -> dict` — varre `system`, `prompt`, `input[*]`,
  `messages[*].content` (str e content-parts). Casou ⇒ **levanta** `SegredoNoPayload`
  (`.achados`). **Falha fechada:** não existe caminho "mascara e devolve". Payload limpo
  volta igual.

### CLI

```
python3 redesign/router/sanitizar.py --padroes     # os 7 padrões (auditoria da régua)
python3 redesign/router/sanitizar.py --autoteste   # fixtures; exit 0 = OK
python3 redesign/router/sanitizar.py --selftest    # stdin = JSON de payload OU texto cru
                                                   # imprime {bloqueado, achados}; exit 3 = bloqueado
```

### Verificado (2026-09-01, offline)

- `--padroes` == `bash -c 'source scripts/varredura_segredo.sh; printf "%s\n" "${PADROES_SEGREDO[@]}"'` — sem diferença.
- `--autoteste`: os 7 padrões casam um positivo cada; 4 casos de menção-não-valor
  (`"o padrão sk-[A-Za-z0-9]{20,} casa..."`, `"aki de manhã"`, ...) passam limpos.
- `--selftest` com payload contendo `sk-…` (gerado na hora, não versionado) → `bloqueado:
  true`, exit 3, `trecho_redigido: "sk-7…[33 chars]"`. Payload limpo → exit 0.

### O que falta (P1-02, quando o OmniRoute existir)

Ligar no egresso: (A) policy de pré-request nativa do OmniRoute, ou (B) proxy fino
`redesign/router/proxy.py` em `127.0.0.1:20127` que chama `sanitizar_payload` e repassa
para `:20128`. Depois os testes de integração (curl + `tcpdump`).

## Outros arquivos da Fase 1 (ainda não criados)

- `proxy.py` — opção B da P1-02.
- `PROVEDORES.md` — P1-03 (lista curada do pool nuvem, limites, combos).
- `conselho_via_omniroute.md` — P1-04 (antes/depois do `conselho_remoto.py`).
