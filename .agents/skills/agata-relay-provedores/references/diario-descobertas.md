# Diário de descobertas

Entradas novas vão ao final. Não apagar nem reescrever registros anteriores.

## 2026-10-27 — foco, espera e leitura

- Gemini só respondeu em teste quando sua aba Chromium ficou visível; o executor passou a focar temporariamente a aba antes de enviar.
- Página pesada demorou mais de 30 segundos; protótipo usou readiness até 90 s, estabilidade de 8 s e limite de resposta de 240 s.
- Z.ai obteve resposta formal num retry após timeout. Isso não autoriza repetir automaticamente o prompt: transporte incerto precisa de revisão humana.
- Um adaptador genérico de Grok capturou o prompt ecoado; validar que a resposta é nova e do assistente.
- ChatGPT exigiu atualizar seletores para o renderer vigente. DOM de provedor pode mudar sem aviso.

## 2026-10-28 — Kimi e controles do provedor

- O Kimi exibiu popup do próprio serviço sobre excesso de usuários e oferta de prioridade por assinatura. Classificar como indisponibilidade/capacidade do provedor, não falha de autenticação.
- Não contornar capacidade, paywall, CAPTCHA ou limite. Não abrir abas auxiliares automaticamente; a extensão opera somente em abas existentes.

## 2026-10-29 — proposta para a extensão oficial

- A proposta migra o envio por API para interação DOM nas abas Chromium permitidas, mantém aprovação humana por prompt e valida resultado por site/tarefa/lease.
- O inventário da extensão informa somente IDs de host detectados; não comprova login nem prontidão. Abas ausentes não são criadas e o perfil persistente fica intacto.
- Validação local em worktree descartável passou; nenhum prompt real foi enviado e a extensão oficial ainda não foi recarregada/testada nos provedores.
- Os nove adaptadores ficam `experimental` até confirmação de resposta formal na versão oficial. As descobertas históricas acima não bastam para declarar qualquer modelo verde hoje.
