# Operator Console offline — SDD fase 0

Status: rascunho para revisão humana; não autorizado para aplicação.

## Objetivo

Oferecer uma superfície local e somente leitura para inspecionar um pacote Project Kit, exibindo proveniência, capacidades, revisões e drift sem criar uma nova fonte de verdade.

## Escopo

- carregar um diretório local via `webkitdirectory`;
- ler `provenance.json`, `capabilities.md`, `drift-report.md` e arquivos `packet.md`;
- mostrar estado explícito quando o pacote estiver ausente, inválido ou não medido;
- manter a operação sem rede, sem execução de comandos, sem escrita de artefatos e sem aprovação automática;
- oferecer navegação local entre Visão, Capacidades, Revisões e Drift.

## Fora de escopo

- verificar criptografia ou recalcular hashes do pacote;
- alterar arquivos do pacote;
- executar ações, aprovar decisões ou publicar resultados;
- depender de fontes externas para carregar fontes, dados ou lógica.

## Invariantes de segurança

1. A interface é read-only.
2. Ausência ou erro de `provenance.json` deve ser visível e não pode ser tratado como integridade confirmada.
3. Dados não medidos devem permanecer rotulados como “não medido”.
4. A interface não deve fazer chamadas de rede nem executar código vindo do pacote.

## Critérios de aceite

- [ ] abrir `index.html` localmente sem servidor;
- [ ] selecionar um pacote válido e exibir objetivo, raiz, quantidade de arquivos, origem e frescor;
- [ ] exibir “PACOTE INVÁLIDO” quando `provenance.json` não existir;
- [ ] exibir “INTEGRIDADE NÃO MEDIDA” quando o JSON for inválido;
- [ ] manter as abas funcionais sem recarregar a página;
- [ ] não haver escrita, execução de comandos ou dependência funcional de rede;
- [ ] validar o JavaScript com `node --check` e o patch com `git diff --check`.

## Lacunas e riscos

- A integridade ainda é apenas declarada como não medida; não há verificação criptográfica.
- A renderização de conteúdo do pacote exige revisão de segurança contra injeção de HTML.
- Não há revisão independente registrada.
- O diff proposto ainda não possui aprovação assinada correspondente.

## Decisões pendentes

- aceitar ou rejeitar a renderização de conteúdo local com HTML bruto;
- definir se a fase 0 deve incluir teste automatizado de ausência de rede;
- aprovar o escopo e autorizar uma revisão independente;
- assinar o diff exato somente após a consolidação das revisões.

## Drift inicial

Ainda não medido. A comparação entre esta especificação e o comportamento implementado deve ocorrer depois da decisão humana e dos testes.
