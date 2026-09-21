#!/usr/bin/env bash
# Extraido de scripts/perimetro.sh (item 10 do plano de mitigacao da
# auditoria do Marcos, MEMORIAS (437)) -- corte-e-cola, corpo identico ao
# de antes, nao e reescrita de logica.

# --- P-8 -----------------------------------------------------------------
# Quarentena de mudança estrutural (item 6, documento do Humano
# 20/08/2026, proposta do Marcos, MEMÓRIAS (218)). O BURACO que isto
# fecha: até aqui, o executor escreve em canon, comita e empurra -- o
# Humano fica sabendo DEPOIS. Nenhuma checagem P-1 a P-7 cobria isso;
# mesma classe do incidente de MEMÓRIAS (214) (sincronizar-estado.sh
# publicando sozinho apesar do próprio cabeçalho dizer que não).
#
# Escopo, proporcional de propósito (ordem do Humano):
#   QUARENTENA OBRIGATÓRIA -- muda COMPORTAMENTO: REGRAS.md, PROJETO.md,
#   scripts/*, .githooks/*
#   SEM quarentena -- só REGISTRA o que já aconteceu: MEMÓRIAS.md,
#   ONDE_ESTAMOS.md, INDICE_MEMORIAS.md, .hidrata.md (gerado)
# Motivo da linha: registro errado se corrige com entrada nova -- é pra
# isso que append-only existe. Comportamento errado, não.
#
# ACHADO 04/09/2026 (Camada C, auditoria dos pareceres gpt-5.6-terra +
# Qwen): testado AO VIVO -- sujar redesign/router/seth_escriba.py, `git add`,
# rodar este script, P-8 respondia "OK", sem SUSPEITO nem FALHA. O padrão
# abaixo nunca cobriu redesign/router/*.py (gateway, sanitizador, o único
# caminho de escrita da Seth), redesign/mcp/*.py, redesign/librechat/*.mjs
# nem redesign/systemd/* -- exatamente o código que faz a sanitização de
# segredo, o portão de hidratação e a trava de append-only. Uma sessão
# comprometida (ou um bug) podia reescrever qualquer um deles e commitar sem
# proposta nem APROVADO-. Ampliado abaixo; teste de regressão fica em
# propostas/aplicadas/ (o par .diff/APROVADO- que aplicou esta mudança).
#
# Mecanismo: propostas/<nome>.diff (a mudança, cabeçalhos `--- a/` /
# `+++ b/` de verdade) + propostas/APROVADO-<nome> (criado pelo Humano
# == aprovação). Sem o par cobrindo o caminho staged, o commit FALHA.
# Ver propostas/README.md pro mecanismo completo, incluindo o risco
# residual registrado sem suavizar: o marcador é um arquivo que o
# próprio executor tem permissão técnica de criar -- P-8 impede
# automação agindo sem ninguém perceber, não impede contorno deliberado.
_p8_eh_comportamento() {
  case "$1" in
    REGRAS.md|PROJETO.md|scripts/*|.githooks/*|config/*) return 0 ;;
    # A raiz de confiança da aprovação assinada (MEMÓRIAS (366)): trocá-la
    # é mudança de comportamento tanto quanto trocar um script. A
    # verificação em _p8_assinatura_ok usa a versão de HEAD, nunca a
    # working-tree -- uma troca staged não autoaprova a própria troca.
    propostas/.allowed_signers) return 0 ;;
    redesign/router/*|redesign/mcp/*|redesign/librechat/*.mjs|redesign/librechat/*.yaml|redesign/systemd/*) return 0 ;;
    # Lacuna achada em (340)/(341), fechada 06/09/2026: redesign/grafo/* (nó real
    # do loop de governança) e redesign/librechat/*.yml (docker-compose, só .yaml
    # estava coberto) mudavam comportamento sem quarentena. *.py/*.sh cobre
    # subpasta também (case casa "/"); *.md/*.gbnf ficam de fora de propósito --
    # varredura real mostrou 17 arquivos afetados, nenhum com aprovação prévia,
    # nenhum trava retroativo. Autorização do Humano, texto explícito.
    redesign/grafo/*.py|redesign/grafo/*.sh|redesign/librechat/*.yml) return 0 ;;
    # Buracos medidos em 09/09/2026, mesma classe do achado de 04/09 que
    # trouxe redesign/router/* pra cá -- código de controle que ficou de fora:
    #   redesign/obsidian/*.py  ro_proxy.py É o serviço que força read-only
    #                           sobre o vault (do_PUT/do_PATCH/do_DELETE ->
    #                           403) e injeta o bearer do Obsidian. Trocá-lo
    #                           abre escrita no vault sem aprovação nenhuma.
    #   SELOS.txt               raiz de confiança do P-14. Sem isto, apagar
    #                           uma linha do SELOS + reescrever o chunk frio
    #                           correspondente, no MESMO commit, passa: as
    #                           duas pernas do P-14 iteram o arquivo mutilado
    #                           e o chunk simplesmente some do relatório.
    #                           (O outro lado deste conserto está no próprio
    #                           p14_frio_imutavel, que agora lê HEAD:SELOS.txt.)
    #   .gitignore              é a PRIMEIRA linha de defesa que o P-11 cita
    #                           no próprio comentário -- editá-la para
    #                           destravar um silo não exigia aprovação.
    #   models/manifest.json    lista de recursos que o P-12 usa como régua de
    #                           backup; mexer nela muda o que "estar coberto"
    #                           significa.
    redesign/obsidian/*.py|SELOS.txt|.gitignore|models/manifest.json) return 0 ;;
    # Buraco achado implementando o item 7 do plano de mitigacao da auditoria
    # do Marcos (MEMORIAS (437), "segunda linha de enforcement remota"):
    # .github/workflows/*.yml executa codigo arbitrario a cada push, no
    # runner do GitHub -- muda comportamento tanto quanto um script daqui,
    # e nao estava coberto. Fechado ANTES de criar o primeiro workflow, nao
    # depois -- senao o proprio workflow entraria sem aprovacao.
    .github/*) return 0 ;;
    # Buraco achado 21/09/2026 fazendo o item 5 do plano de ação da auditoria
    # de Marcos (MEMÓRIAS (500)/(502)/(503)): redesign/igpu/*.py
    # (whisper_server.py, embeddings_server.py -- servem STT/embeddings na
    # iGPU, leem arquivo por caminho pedido no corpo do request) nunca esteve
    # nesta lista -- mesma classe dos buracos de 04/09 e 09/09 acima (código
    # de controle real, fora do padrão scripts/*). Confirmado o mesmo teste ao
    # vivo de antes: sujar redesign/igpu/whisper_server.py sem propostas/
    # nenhuma, `git add`, rodar perimetro.sh -- P-8 dizia OK antes deste
    # conserto (ver commit desta entrada pro antes/depois).
    redesign/igpu/*.py) return 0 ;;
    *) return 1 ;;
  esac
}


_p8_assinatura_ok() {
  # Assinatura ssh de propostas/APROVADO-<nome> sobre o .diff (desde
  # MEMÓRIAS (366)). Sem propostas/.allowed_signers no repo: assinatura
  # NÃO exigida -- modo compat da janela em que o par de chaves ainda
  # não foi gerado. Com .allowed_signers presente: exige bloco
  # `BEGIN SSH SIGNATURE` válido, principal `agata-humano`, namespace
  # `agata-aprovacao-p8`, mensagem = "<sha256 do .diff>  <nome>".
  # A mensagem carrega o hash do .diff -> editar o .diff depois de
  # assinado quebra a verificação. Verificar não precisa da passphrase;
  # só assinar (scripts/aprovar.sh, mão do Humano) precisa.
  local aprovado="$1" diff_abs="$2" nome="$3"
  local signers signers_tmp="" sig="" rc=1

  # Raiz de confiança = a versão JÁ COMMITADA de propostas/.allowed_signers
  # (HEAD:), nunca a working-tree -- senão uma troca de .allowed_signers
  # staged no mesmo commit poderia autoaprovar a própria troca. Rotação de
  # chave: assina-se o .diff da rotação com a chave ATUAL (a de HEAD), que
  # é o que esta verificação usa. Primeiro commit que introduziu
  # .allowed_signers não tinha HEAD: -> caía no working-tree (bootstrap).
  if git cat-file -e HEAD:propostas/.allowed_signers 2>/dev/null; then
    signers_tmp="$(mktemp)"
    git show HEAD:propostas/.allowed_signers > "$signers_tmp" 2>/dev/null
    signers="$signers_tmp"
  elif [ -f "$(pwd)/propostas/.allowed_signers" ]; then
    signers="$(pwd)/propostas/.allowed_signers"
  else
    return 0   # nem HEAD: nem working-tree -> modo compat (par de chaves ainda não existe)
  fi

  local dsha msg
  dsha="$(sha256sum "$diff_abs" | awk '{print $1}')"
  msg="$(printf '%s  %s' "$dsha" "$nome")"

  if ! command -v ssh-keygen >/dev/null 2>&1; then
    echo "P-8: ssh-keygen ausente -- não dá pra verificar a assinatura de $aprovado"
  elif ! grep -qxE "diff-sha256: $dsha" "$aprovado" 2>/dev/null; then
    echo "P-8: $aprovado -- linha 'diff-sha256:' ausente ou diferente do .diff atual (diff editado depois de assinado?)"
  else
    sig="$(mktemp)"
    awk '/-----BEGIN SSH SIGNATURE-----/,/-----END SSH SIGNATURE-----/' "$aprovado" > "$sig"
    if ! [ -s "$sig" ]; then
      echo "P-8: $aprovado sem bloco de assinatura ssh -- gere com scripts/aprovar.sh (PROJETO.md, \"Quarentena estrutural\")"
    elif printf '%s' "$msg" | ssh-keygen -Y verify -f "$signers" -I agata-humano \
           -n agata-aprovacao-p8 -s "$sig" >/dev/null 2>&1; then
      rc=0
    else
      echo "P-8: assinatura inválida em $aprovado (chave não confere com a raiz de confiança em HEAD:propostas/.allowed_signers, ou mensagem adulterada)"
    fi
  fi

  [ -n "$sig" ] && rm -f "$sig"
  [ -n "$signers_tmp" ] && rm -f "$signers_tmp"
  return "$rc"
}


_p8_arquivo_aprovado() {
  # Conserto de 22/08/2026 (achado testando `ab1-projeto.diff`, ver
  # MEMÓRIAS -- "aprovado" deixava de expirar: qualquer arquivo já
  # citado no cabeçalho de QUALQUER .diff aprovado, alguma vez na
  # história, ficava isento de P-8 pra sempre, porque `propostas/
  # aplicadas/` nunca é limpo (é o registro histórico, por desenho) e a
  # checagem antiga só olhava PATH, nunca CONTEÚDO. Confirmado com uma
  # edição trivial e sem relação nenhuma passando pela quarentena.
  #
  # Novo critério: "aprovado" só conta se aplicar o .diff candidato à
  # versão HEAD (pai) deste arquivo reproduz, byte a byte (hash do
  # blob), o que está staged agora. Path não decide mais nada sozinho
  # -- só entra na lista de candidatos a testar. Um .diff antigo, já
  # consumido, só vai bater essa checagem se o arquivo staged agora for
  # EXATAMENTE o resultado daquela mudança antiga -- o que não acontece
  # numa edição nova e diferente, mesmo no mesmo caminho.
  local f="$1" staged_blob diretorio aprovado nome diff_path
  local tmp resultado_blob diff_abs repo_raiz eh_delecao=0

  # --verify --quiet: exige UM objeto válido e sai != 0 SEM ecoar o argumento
  # quando não há (git rev-parse "cru" ecoa o arg no stdout e sai 128 -- isso
  # enchia $staged_blob com lixo e pulava o ramo de deleção).
  if ! staged_blob="$(git rev-parse --verify --quiet ":$f" 2>/dev/null)" \
     || [ -z "$staged_blob" ]; then
    # Sem blob staged. Ou o arquivo saiu do commit (P-8 não o checa), ou
    # está staged como DELEÇÃO -- e P-8 tem que poder aprovar deleção de
    # arquivo de comportamento igual aprova modificação: por um .diff
    # ASSINADO cujo hunk pra este path seja uma deleção total. Antes,
    # `|| return 1` aqui bloqueava TODA deleção sem caminho de aprovação
    # (achado em MEMÓRIAS (403); conserto autorizado em (407) com 2a
    # opinião do Conselho Remoto). Renomear = git vê delete(path velho) +
    # add(path novo) -- mas isso só é verdade com `--no-renames`. Sem ele, a
    # detecção de rename do git (LIGADA por padrão) colapsa os dois lados
    # num único R e mostra APENAS o path novo: o lado "delete" simplesmente
    # não aparece, e este ramo nunca dispara.
    # MEDIDO 09/09/2026 (vermelho/verde, clone descartável): editar
    # redesign/router/sanitizar.py no lugar -> SUSPEITO (P-8), correto;
    # `git mv redesign/router/sanitizar.py extras/` -> P-8 SILENCIOSO, e o
    # sanitizador (único ponto que tira segredo do payload antes de sair pra
    # provedor externo) saía do caminho vivo sem nenhum APROVADO-. Qualquer
    # arquivo de comportamento podia deixar a quarentena por renomeação.
    # Por isso `--no-renames` aqui E em p8_quarentena -- os dois têm que
    # enxergar o mesmo conjunto de paths, senão o furo volta por um lado só.
    if git -c core.quotepath=false diff --cached --no-renames --name-only --diff-filter=D 2>/dev/null | grep -qxF -- "$f"; then
      eh_delecao=1
    else
      return 1
    fi
  fi
  repo_raiz="$(pwd)"

  for diretorio in propostas propostas/aplicadas; do
    [ -d "$diretorio" ] || continue
    for aprovado in "$diretorio"/APROVADO-*; do
      [ -e "$aprovado" ] || continue
      nome="$(basename "$aprovado")"
      nome="${nome#APROVADO-}"
      diff_path="$diretorio/${nome}.diff"
      [ -f "$diff_path" ] || continue
      # Filtro barato antes do caro: só tenta aplicar diffs que sequer
      # mencionam este caminho no cabeçalho.
      grep -qE "^(\+\+\+ b/|--- a/)$(printf '%s' "$f" | sed 's/[.[\*^$/]/\\&/g')\$" "$diff_path" 2>/dev/null || continue

      diff_abs="$repo_raiz/$diff_path"
      tmp="$(mktemp -d)" || continue
      mkdir -p "$tmp/$(dirname "$f")"
      # Conserto de 23/08/2026 (achado testando `harness-a1-trace.diff`,
      # arquivo NOVO): criar um placeholder vazio aqui fazia `git apply`
      # recusar diffs de "novo arquivo" (`--- /dev/null`) com "already
      # exists in working directory" -- esse tipo de diff exige que o
      # caminho NÃO exista pra aplicar. Não criar nada quando o arquivo
      # não existe em HEAD deixa o próprio `git apply` criar o arquivo,
      # igual faria num `git apply` real contra o repositório.
      if git cat-file -e "HEAD:$f" 2>/dev/null; then
        git show "HEAD:$f" > "$tmp/$f" 2>/dev/null
      fi

      if (cd "$tmp" && git apply --include="$f" "$diff_abs") >/dev/null 2>&1; then
        if [ "$eh_delecao" -eq 1 ]; then
          # Aplicar o .diff a HEAD:$f fez o arquivo SUMIR == a deleção
          # staged. `git apply` já validou o CONTEÚDO do hunk (as linhas
          # `-` da deleção têm que bater com HEAD:$f, senão recusa) --
          # não basta o cabeçalho citar o path.
          if [ ! -e "$tmp/$f" ] && _p8_assinatura_ok "$aprovado" "$diff_abs" "$nome"; then
            rm -rf "$tmp"
            return 0
          fi
        else
          resultado_blob="$(git hash-object "$tmp/$f" 2>/dev/null)"
          if [ "$resultado_blob" = "$staged_blob" ] && _p8_assinatura_ok "$aprovado" "$diff_abs" "$nome"; then
            rm -rf "$tmp"
            return 0
          fi
        fi
      fi
      rm -rf "$tmp"
    done
  done
  return 1
}


p8_quarentena() {
  local staged f ruim=0
  # `--no-renames` é load-bearing, não cosmético: sem ele um rename aparece
  # só com o path NOVO, e mover um arquivo de comportamento pra fora dos
  # padrões de _p8_eh_comportamento tira ele da quarentena sem APROVADO-
  # nenhum (bypass medido em 09/09/2026 -- ver o comentário longo em
  # _p8_arquivo_aprovado). Com ele, os dois lados do rename entram na
  # checagem, e os dois hunks precisam estar no MESMO .diff assinado.
  staged="$(git -c core.quotepath=false diff --cached --no-renames --name-only)"
  [ -z "$staged" ] && return 0
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    # 2ª passada do índice final (item 9 do plano de ação da auditoria do
    # Marcos, MEMÓRIAS (500)/(502)/(505)/(506)): `.githooks/pre-commit` roda
    # `p8_quarentena` de novo DEPOIS da âncora de SHA reescrever REGRAS.md/
    # PROJETO.md/MEMÓRIAS.md -- sem isto, a 2ª passada bloquearia TODO commit
    # (a âncora muda os 3 em todo commit, e ninguém assina isso, nem devia:
    # é bookkeeping mecânico, não mudança de comportamento). `_P8_EXCLUIR`
    # (uma linha por caminho) só é setado pelo próprio hook, só na 2ª
    # chamada -- a 1ª (T0, antes da âncora rodar) nunca o define, então
    # continua vendo os 3 arquivos normalmente se o AUTOR tivesse mudado
    # algo neles por conta própria. A guarda de integridade de âncora
    # (.githooks/pre-commit) já prova, byte a byte, que nada MAIS mudou
    # nesses 3 arquivos além do bloco da âncora -- é essa prova que torna
    # a exclusão aqui segura, não uma isenção às cegas.
    if [ -n "${_P8_EXCLUIR:-}" ] && grep -qxF "$f" <<< "$_P8_EXCLUIR"; then
      continue
    fi
    if _p8_eh_comportamento "$f"; then
      if ! _p8_arquivo_aprovado "$f"; then
        echo "SUSPEITO (P-8): '$f' muda comportamento e está staged sem propostas/APROVADO-<nome> correspondente cujo diff, aplicado ao HEAD deste arquivo, reproduza exatamente o conteúdo staged (o .diff em propostas/ precisa citar este caminho nos cabeçalhos E bater byte a byte). Crie a proposta, peça aprovação do Humano (propostas/README.md), ou tire este arquivo do commit."
        ruim=1
      fi
    fi
  done <<< "$staged"
  return "$ruim"
}

