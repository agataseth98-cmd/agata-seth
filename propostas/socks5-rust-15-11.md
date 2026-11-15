# SOCKS5 do navegador em Rust e camada Rust ligada no navegador (`socks5-rust-15-11`)

Proposta P-8 de `socks5-rust-15-11`. Diff: `propostas/socks5-rust-15-11.diff` (9 arquivos; sha256 `949c70b2a9bea50c18765404222c411b4dac23e98a8f482ef4b0f2c656cefe77`). Base: `origin/main`.

Decisões do Humano em 15/11/2026: "Propor ligar" a segunda opinião do Rust nos serviços; fazer o SOCKS5 em Rust "Agora"; encerrar o T2 sem avaliação às cegas.

O que muda:
1. **SOCKS5 em Rust** (`redesign/rust/egress/src/socks5.rs` + binário `egress-socks5`, só biblioteca padrão): espelho de `egress_proxy.py`. Só CONNECT, sem autenticação; resolve uma vez, recusa se qualquer IP não for global e conecta ao IP validado.
2. **`EgressProxy`** (`egress_proxy.py`) usa o binário Rust quando `AGATA_EGRESS_RUST_SOCKS5` aponta para ele; sem binário, ou se ele falhar ao subir, volta ao Python e avisa.
3. **`navegador-mcp.service`** liga as duas variáveis (`AGATA_EGRESS_RUST` e `AGATA_EGRESS_RUST_SOCKS5`) apontando para `~/.local/bin`.
4. **`scripts/instalar_egress_rust.sh`** compila e instala os dois binários.
5. **CI `rust-egress`** passa a cobrir `egress_proxy.py`; `testar_egress_rust.py` sobe o binário real e confere a recusa.

Medido em 15/11/2026: `cargo test --locked` com 5 testes novos do SOCKS5 passando (39 no total); `testar_egress_rust.py` OK (o binário recusa 127.0.0.1, 10.0.0.5 e 169.254.169.254 com status 2; volta ao Python sem binário); `testar_egress_proxy.py` OK. Ao vivo com curl pelo SOCKS5 Rust: example.com respondeu 200 e localhost foi recusado.

Não medido: o navegador real (Playwright + Brave) passando pelo SOCKS5 Rust. Isso exige instalar os binários, copiar a unit para `~/.config/systemd/user/` e reiniciar o `navegador-mcp` depois da aplicação.

Reversão: `git revert` do commit de aplicação; sem os binários, o navegador já volta ao Python.
