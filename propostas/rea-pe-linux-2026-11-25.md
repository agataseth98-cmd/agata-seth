# Proposta P-8: análise estática de PE pelo REA

Classe: Comportamento

## Objetivo

Adicionar ao wrapper do REA quatro inspeções estáticas e somente de leitura para arquivos PE32/PE32+: `inspect-pe-imports`, `inspect-pe-certificates`, `inspect-pe-resources` e `inspect-pe-load-config`. Cada comando recebe exatamente um caminho absoluto e `--json`. O wrapper usa o `rea-agents` 6.8.0 já presente no cache local; não instala nem atualiza pacotes.

Os 14 comandos JavaScript/web existentes permanecem permitidos. A guarda do wrapper recusa argumentos adicionais e cabeçalhos PE ausentes, truncados ou incoerentes entre Machine e PE32/PE32+.

## Limites e interpretação

São usados os limites padrão do REA 6.8.0: arquivo de 64 MiB; imports com 256 DLL/descriptors, 8192 funções e texto retido até 16 MiB; 8 certificados; 16384 entradas de recursos; 64 callbacks TLS. O wrapper não encaminha overrides desses limites. Erro, ausência de diretório ou cobertura parcial permanecem distintos.

EXE, DLL e SYS são categorias declaradas pelo operador. Estes quatro resultados não confirmam por si sós que um arquivo seja DLL ou tenha papel de driver; `.sys`, nome e imports isolados não provam que seja driver. Certificado não equivale a assinatura Authenticode válida; callback TLS listado não prova execução.

Reconstrução de recursos para Linux em Rust permanece fora deste lote e exige SDD e decisão próprios. Não há decompilação, pseudocódigo, geração de Rust ou execução do PE.

## Testes e evidência

Resultado registrado para este lote: CI local 95/95 e revisão independente 10/10. Os testes da área verificam a allowlist JavaScript/web, argv do fake CLI, fixtures PE32/PE32+ determinísticas, campos e ausências do REA 6.8.0, recusas de cabeçalho e limites, integridade SHA-256/tamanho e ausência de arquivos derivados. O CI do PR ainda deve confirmar esta revisão antes da assinatura.

SHA-256 do `propostas/rea-pe-linux-2026-11-25.diff`: `56b25db0b13a97e12c4596d201ec9be66d06814f22ca49cbcb913e91034d82fd`.

## Reversão

Depois da aplicação assinada, a reversão é uma proposta P-8 que remove os quatro comandos PE, os testes PE e a documentação PE. Os 14 comandos JavaScript/web permanecem. Nenhum pacote ou arquivo PE precisa ser alterado.

Comando de assinatura, após o CI da proposta passar e após revisar o diff:

`bash scripts/aprovar.sh rea-pe-linux-2026-11-25`
