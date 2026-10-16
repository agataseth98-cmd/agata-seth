# Manifesto técnico candidato — revisão Codex 16/10/2026

Estado: pacote de fechamento para UMA assinatura humana; não assinado nem aplicado. Inclui o registro canônico (entrada (728) de MEMÓRIAS e parágrafo de ONDE_ESTAMOS). O objeto assinado é o sha256 do `.diff`, conferido pelo Humano contra o recibo externo.

Base real: `9cc0a6ce15132911010f1970c1752076ddda9dd8`.

Escopo: fiscal proporcional de PR com correções de âncora/transporte; auxiliar integral; hook worktree; voz candidata; inventário/atualização; consulta sem manutenção implícita; trava estável do escriba; dois testes offline e inclusão no CI. Memória temática, aliases, corrige estruturado, ACL, resolvedor temporal, F0 e métricas continuam no plano, não implantados por este candidato.

Manifesto autoexcluído da identidade abaixo: caminho exato `propostas/MANIFESTO-governo-integridade-20261016.md`. Não contém hash de si nem do diff. A árvore abaixo representa payload ANTES desta inclusão, não árvore final pós-hook. Recibo externo registra hash completo do diff e árvore com manifesto. Nenhum outro caminho foi excluído desta tabela de payload.

Árvore de construção antes do manifesto: `9bf658fb06b1d85e39fea33fb84efdceab890f54` (baseline sintético com mesmos blobs da base real, antes de âncoras/transporte).

| caminho | modo | blob | sha256 |
|---|---|---|---|
| .githooks/post-commit | 100755 | 44aec8aab4679ed699132cf6421a117e0207c9d3 | 5868b3a64e527e3c6f2db1907cd3fb081599765c410e54da35ecdd1a37c85116 |
| .github/dependabot.yml | 100644 | b82e0b9b1a02aa9d774a0dce38d9098f2c519538 | ae7dd24fb7087d34dd8a2eb4192a917f6d3d5800c80084ad01898444c8e84b48 |
| .github/workflows/fiscal-p8.yml | 100644 | 9b27d87b8ab6a4ffed7fa46a8d214204d4891ce5 | 7f21891de7b95418375f3f5b4ecdf0a5730dc66b040e3df94f96b62b7942dbd0 |
| .github/workflows/perimetro.yml | 100644 | d6a749c9b0dec9ca6a3699c8cc2a0ebebe260a21 | 48f203558a548f5f7aed7a08f25731414321f97c312c3669cb74988b7cab14ff |
| .gitignore | 100644 | e70ed4c7035cc36e17e6bb00564a544eb2d80c47 | c953c2f8def3b5ad115d6bdacfcc4ff65147321be381a8fddb143eac6de6613b |
| MEMÓRIAS.md | 100644 | 9f987656dd1a902800675b7f6f010eb33682d0fa | 9ff66c4ec3ff76d95e50431a6e9dcb98dc10a25dffc394e7ba544fee358a4b53 |
| ONDE_ESTAMOS.md | 100644 | 7f35ec9277cc343b0a5ac5bc40cb6060807889f5 | 0a6fc7386273786103ddb4923e6ffd480bf39e3062eac2b5b9e729975f47ec75 |
| PROJETO.md | 100644 | 44c490471718c5a053c0bc3709088bd2d48fae52 | 139bd0ebc3eb082bbf02bebb79e2d5e2c2e5f6e4df991c759a4dc4b53615a3b8 |
| config/componentes-externos.txt | 100644 | 7d5813dc009f16e1ab668cf1d5ba5596d7304d70 | 12b4bd8a142df261e6ddec464d5527500e27fafd934b6b9b512d39559fb39510 |
| redesign/router/seth_escriba.py | 100644 | fc24dc792aa02393bedd5ce5087490c7e505e66d | baf2cae5887f3641886530698a650df02bbc0fbfa42923970013d19700fd4239 |
| redesign/router/seth_verificador.py | 100644 | 54d67f3fde34a892ef7883fd9c1ef3548298b8e0 | c255b93c54b8b3aeabc623d403dbf6e6f1c299173d08d472171cbb437433e181 |
| redesign/router/tts-piper/agata-last.sha256 | 100644 | 068f95098e4da9be7dcd5f9bfaf741d0bc58f781 | 64611bc962068c92d5694266b1b2a7c67907105dae181d5f9feb9c6d01ddb503 |
| redesign/router/tts-piper/instalar-agata.sh | 100755 | 784a5209ea3acd6b9a9dd38d634bb4d19cfdd9f0 | ce5e45046a4941409b56fa6199b2f814eaf95319bae7f6e24cd5c4a1d642817e |
| redesign/router/tts_piper.py | 100755 | a608478394fee5a5904c8f5d27f6ded96521fa6d | fe1790a85cc4d0e0ddbe7c3f3b68a2187709dcd4394de67f79aba2030719fc3d |
| scripts/agata_busca.sh | 100755 | cb0600ea495592eb00a22f80534086f8adf52253 | 9655909a229e55e11f6a3f5159d3c78b61a425a1390b3133bb2355f093a48489 |
| scripts/atualizar.sh | 100755 | d39a9b1ca6482f85f32ff81c18fa95a3a5831188 | 3634f5918bc94bafb31dbc30d4c11a122b436c2b4074bc16d36922a54083ef72 |
| scripts/busca_semantica.py | 100644 | 81055fa1b925628be954c0150ab7c1b54677cb7a | ef2dca8890c3403a2dd329cd6638ba7c18ac97d49655162498720636a0fbeac8 |
| scripts/inventario_componentes.py | 100755 | 6236f3321ed07df53f3edfe3c67e8e0b8d0dbe22 | adb14263707dbfea88fd401ba7a3ee0280be34ac6772f3c0282a921c517586f3 |
| scripts/p8_integral.py | 100755 | 24cc9b432aa7b14bd9a6f1989168b675c1d15e71 | 92e6913c3ee789dcf65b21a5df329c114a651673626ad0911dc4fa67393beb38 |
| scripts/p8_verificar_pr.sh | 100755 | e9e8905434e9688d0a59abc950b0a8d705db901d | e5e970b92c32b84cff69513e3b4889b0b19e53f6a904f1369f17e057652049a9 |
| scripts/testar_atualizar.py | 100755 | 14d52c12717f255694b1b4437412b745eec43482 | 8b0f6e5d8f82758fff921450e79c590b32832f9bc7d2b5fe84719092634f6d68 |
| scripts/testar_memoria_leitura.py | 100644 | 0e94119403f59aed53c2de4a1792899b60d4156d | de85d039bd593bfbfe68d7bbdb728d8736528df5a20c92a7a2f68d88ed9dbea9 |
| scripts/testar_p8_verificar_pr.py | 100755 | 357be575a451a13ee393221236618f0346b43175 | 170f74a5cd9546eea70d68ac4a76b377d6ae141d46867fda5db53c8396198014 |
| scripts/testar_post_commit.py | 100755 | aaa3ddbb302487bdd362a22370bef504fe6b03dd | bddcabb5021290491ab98277384b031bcd1f57c75e6da7e31ed5b2ebe47b2e39 |
| scripts/testar_trava_escriba.py | 100644 | 5bdd42836f90e029f59c00dfefb6a56da334067b | cf4a997c8d0743e11e01192751ae1d1f5e5bbe91758153d5a20b5079715fdc89 |

Provas externas disponíveis: integralidade29, fiscal25; contraprovas F1/F2 agora rejeitadas; memória10 e escriba5 em checkout descartável. São resultados anteriores identificados por fontes/recibos; os ensaios integrados desta construção precisam constar no recibo externo, não são presumidos aqui.

Limites: nenhum CI remoto/obrigatoriedade observado; nenhum serviço ativado; nenhum aceite auditivo presumido. Escriba não resolve escritores não cooperativos, troca de caminhos pós-abertura e fsync de diretório. Busca não faz manutenção: escrita sem vetor precisa de pesquisa textual até post-commit/manutenção autorizada. Schema/vetores inválidos não são resolvidos integralmente. Derivados por snapshot fixo não implementados. Cofre/canais/ACL/temas não implantados.

Antes da aplicação: assinatura humana do diff exato, p8_verificar.sh anterior extraído da base confiável, comparação integral independente. No pacote inaugural, p8_integral não existe em9cc: usar cópia independente previamente revisada e identificada, sem chamar de código anterior. Perímetro novo complementa prova e não se autoautoriza. Aplicação/PR final permanecem com o Humano.

Publicação: adaptar explicitamente o fluxo692 caso registro canônico fique dentro do payload por instrução humana de assinatura do canon. Não afirmar que publicação sódiff é o fluxo padrão original. Drift exige reconstrução/revisão antes da assinatura. Nunca assinar patches futuros desconhecidos.

Volta: preservar história; reversão protegida precisa do portão aplicável. Voz usa PIPER_MODEL para modelo anterior e PIPER_TRATAMENTO=off, sem apagar arquivos. Alteração operacional só pelo ato autorizado correspondente. Desativar check remoto obrigatório antes de eventual reversão do workflow é ato humano.

Refinamento de fechamento: registro canônico por referências; versão detalhada original preservada nos relatórios do Claude. Tabela e identidade acima recalculadas após MEMÓRIAS/ONDE, excluindo apenas este manifesto.
