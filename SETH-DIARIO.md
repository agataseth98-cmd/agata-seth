# Diário da Seth

Espaço próprio da Seth, append-only. Fora do vault derivado (o P-10 não
policia este arquivo) e fora de MEMÓRIAS. Escrito só via a tool `diario_anotar`
(-> `seth_escriba` `POST /diario`); nunca editado nem apagado por ela.
Autorizado pelo Humano: "append only... quero ver como ela se desenvolve.
Eu assumo o risco." (03/09/2026)


---
**2026-09-16 13:29 -0300 (relógio da Máquina)**

[RELATÓRIO] Vulnerabilidade de prompt injection (MEMÓRIAS 420) ainda ativa. Teste reproduzido via script /tmp/repro_injecao_420.py fora do repo, confirmando que `_e_chamada_utilitaria` ainda permite desligar hidratação ao detectar strings externas. Conclusão: vulnerabilidade não mitigada, necessidade de correção conforme proposta em PROJETO.md (linha 385).
