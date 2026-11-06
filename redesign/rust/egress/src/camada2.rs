//! Camada 2 do egress: o que a camada 1 (`classificar_ip`, `validar_url`) não cobre.
//!
//! - `resolver_e_classificar`: resolve o host com `std::net::ToSocketAddrs` e
//!   classifica TODOS os IPs devolvidos; se um for bloqueado, recusa tudo.
//! - `validar_redirect` / `seguir_redirects`: resolve o Location (absoluto ou
//!   relativo) sobre a URL de origem, valida esquema e userinfo e revalida o
//!   DNS do novo destino. Limite de `LIMITE_REDIRECTS` redirecionamentos.
//! - Pinagem: a lista devolvida por `resolver_e_classificar` (e a de
//!   `validar_redirect_com_ips`) é o conjunto já validado. O chamador conecta
//!   em um desses IPs, sem nova resolução.
//!
//! Limitações: não abre conexão, não faz TLS nem HTTP. Host só passa com
//! sintaxe LDH (letras, dígitos, hífen) ou IP literal; o resto é recusado antes
//! do DNS. O parser de URL é o da camada 1 (sem percent-decoding nem IDNA).

use crate::{classificar_ip, destino, validar_url};
use std::net::{IpAddr, ToSocketAddrs};

/// Número máximo de redirecionamentos seguidos; o próximo é recusado.
pub const LIMITE_REDIRECTS: usize = 10;

/// Resolve `host:porta` e classifica todos os IPs. Recusa se qualquer um for
/// bloqueado (mesmo critério de `classificar_ip`) ou se a lista vier vazia.
///
/// Os IPs devolvidos são o conjunto pinado: o chamador conecta em um deles.
pub fn resolver_e_classificar(host: &str, porta: u16) -> Result<Vec<IpAddr>, String> {
    let ips: Vec<IpAddr> = match host.parse::<IpAddr>() {
        Ok(ip) => vec![ip],
        Err(_) => {
            if !host_dns_valido(host) {
                return Err(format!("host inválido para resolução: '{host}'"));
            }
            let resolvidos = (host, porta)
                .to_socket_addrs()
                .map_err(|e| format!("sem resolução DNS para '{host}': {e}"))?;
            resolvidos.map(|sa| sa.ip()).collect()
        }
    };
    if ips.is_empty() {
        return Err(format!("sem resolução para '{host}'"));
    }
    for ip in &ips {
        if let Some(motivo) = classificar_ip(&ip.to_string()) {
            return Err(format!("IP {ip} de '{host}' bloqueado: {motivo}"));
        }
    }
    Ok(ips)
}

/// Valida um redirecionamento e devolve a URL final (sem os IPs).
pub fn validar_redirect(origem: &str, location: &str) -> Result<String, String> {
    validar_redirect_com_ips(origem, location).map(|(url, _)| url)
}

/// Como `validar_redirect`, mas devolve também os IPs validados do novo destino,
/// para o chamador conectar sem nova resolução (pinagem).
pub fn validar_redirect_com_ips(
    origem: &str,
    location: &str,
) -> Result<(String, Vec<IpAddr>), String> {
    let url = url_do_redirect(origem, location)?;
    validar_url(&url)?;
    let (host, porta) = destino(&url)?;
    let ips = resolver_e_classificar(&host, porta)?;
    Ok((url, ips))
}

/// Como `seguir_redirects`, mas devolve, para cada salto (inclusive a URL inicial),
/// a URL e os IPs validados naquele momento. Quem conecta deve usar esses IPs
/// (pinagem), sem resolver o host de novo: evita DNS rebinding entre validação e conexão.
pub fn seguir_redirects_com_ips(
    url_inicial: &str,
    locations: &[&str],
) -> Result<Vec<(String, Vec<IpAddr>)>, String> {
    if locations.len() > LIMITE_REDIRECTS {
        return Err(format!(
            "{} redirecionamentos recebidos; limite é {LIMITE_REDIRECTS}",
            locations.len()
        ));
    }
    validar_url(url_inicial)?;
    let (host, porta) = destino(url_inicial)?;
    let ips = resolver_e_classificar(&host, porta)?;
    let mut saltos = vec![(url_inicial.to_string(), ips)];
    for location in locations {
        let (url, ips) = validar_redirect_com_ips(&saltos[saltos.len() - 1].0, location)?;
        saltos.push((url, ips));
    }
    Ok(saltos)
}

/// Aplica `validar_redirect` em sequência, cada Location sobre a URL anterior.
/// Recusa se houver mais de `LIMITE_REDIRECTS` Locations.
///
/// NÃO é guarda de conexão: valida só nomes, sem resolver o DNS de cada salto.
/// Quem conecta pelo nome depois reconsulta o DNS (DNS rebinding). Para conectar,
/// use `seguir_redirects_com_ips`, que devolve os IPs validados de cada salto.
pub fn seguir_redirects(url_inicial: &str, locations: &[&str]) -> Result<String, String> {
    if locations.len() > LIMITE_REDIRECTS {
        return Err(format!(
            "{} redirecionamentos recebidos; limite é {LIMITE_REDIRECTS}",
            locations.len()
        ));
    }
    validar_url(url_inicial)?;
    let (host, porta) = destino(url_inicial)?;
    resolver_e_classificar(&host, porta)?;

    let mut atual = url_inicial.to_string();
    for location in locations {
        atual = validar_redirect(&atual, location)?;
    }
    Ok(atual)
}

/// Monta a URL absoluta do Location. Absoluto passa como está (a validação
/// de esquema e userinfo fica com `validar_url`).
fn url_do_redirect(origem: &str, location: &str) -> Result<String, String> {
    let loc = limpar(location);
    if loc.is_empty() {
        return Err("Location vazio".to_string());
    }
    let (esquema_loc, _) = crate::separar_esquema(&loc);
    if !esquema_loc.is_empty() {
        return Ok(loc);
    }

    let (esquema, netloc, caminho) = partes_origem(origem)?;
    if loc.starts_with("//") {
        return Ok(format!("{esquema}:{loc}"));
    }

    let (cam, sufixo) = match loc.find(['?', '#']) {
        Some(i) => (&loc[..i], &loc[i..]),
        None => (loc.as_str(), ""),
    };
    let so_caminho = caminho.split(['?', '#']).next().unwrap_or("");
    let caminho_final = if cam.is_empty() {
        if so_caminho.is_empty() {
            "/".to_string()
        } else {
            so_caminho.to_string()
        }
    } else if cam.starts_with('/') {
        normalizar(cam)
    } else {
        let dir = match so_caminho.rfind('/') {
            Some(i) => &so_caminho[..=i],
            None => "/",
        };
        normalizar(&format!("{dir}{cam}"))
    };
    Ok(format!("{esquema}://{netloc}{caminho_final}{sufixo}"))
}

/// Esquema, netloc e caminho (com query/fragment) da origem, já validada.
fn partes_origem(origem: &str) -> Result<(String, String, String), String> {
    destino(origem)?;
    let limpa = limpar(origem);
    let (esquema, resto) = crate::separar_esquema(&limpa);
    let netloc = crate::netloc_de(resto);
    let caminho = &resto[2 + netloc.len()..];
    Ok((esquema, netloc.to_string(), caminho.to_string()))
}

/// Remove `.` e `..` do caminho e preserva a barra final.
fn normalizar(caminho: &str) -> String {
    let barra_final =
        caminho.ends_with('/') || caminho.ends_with("/.") || caminho.ends_with("/..");
    let mut pilha: Vec<&str> = Vec::new();
    for seg in caminho.split('/') {
        match seg {
            "" | "." => {}
            ".." => {
                pilha.pop();
            }
            s => pilha.push(s),
        }
    }
    let mut out = format!("/{}", pilha.join("/"));
    if barra_final && !out.ends_with('/') {
        out.push('/');
    }
    out
}

/// Mesma limpeza de `destino`: tira tab/CR/LF e espaços das pontas.
fn limpar(url: &str) -> String {
    let s: String = url
        .chars()
        .filter(|c| !matches!(c, '\t' | '\r' | '\n'))
        .collect();
    s.trim_matches(|c: char| c <= ' ').to_string()
}

/// Sintaxe de host DNS (rótulos LDH). Vazio, com `:`, `%`, espaço etc. é recusado
/// antes de chamar o resolvedor.
fn host_dns_valido(host: &str) -> bool {
    !host.is_empty()
        && host.len() <= 253
        && host.split('.').all(|rotulo| {
            let b = rotulo.as_bytes();
            !b.is_empty()
                && b.len() <= 63
                && b[0] != b'-'
                && b[b.len() - 1] != b'-'
                && b.iter().all(|c| c.is_ascii_alphanumeric() || *c == b'-')
        })
}
