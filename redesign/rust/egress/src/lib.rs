//! Política de egress/anti-SSRF, camada Rust (primeira fatia da D6).
//!
//! Espelha `scripts/politica_egress.py`:
//! - `classificar_ip` ↔ `_ip_bloqueado` (mesma ordem: global, loopback,
//!   link-local, privado, reservado/outro);
//! - `validar_url` / `destino` ↔ a parte de URL de `_resolver_destino`
//!   (esquema, userinfo, host, porta), SEM DNS.
//!
//! A resolução DNS fica fora da biblioteca: o chamador resolve `destino().0`,
//! classifica cada IP com `classificar_ip` e só então abre o socket com um dos
//! IPs validados (pinning, sem janela TOCTOU).
//!
//! Limitações conhecidas (ver também o relatório da fatia):
//! - Parser de URL mínimo, só para esquema, netloc (userinfo, host, porta).
//!   Não valida path/query/fragment, não faz percent-decoding nem IDNA.
//! - Tabela de faixas IPv4/IPv6 é um recorte do CPython 3.14: IPv4 completo
//!   na lista de privadas; IPv6 com os prefixos principais. Verdicts conferidos
//!   contra o Python em uma amostra, não em toda a faixa de endereços.
//! - Entrada IP inválida devolve motivo de bloqueio (fail-closed). O Python
//!   levantaria ValueError.
//! - Porta 0 cai no padrão (80/443), como `partes.port or default` no Python.

use std::net::{IpAddr, Ipv4Addr, Ipv6Addr};

const ESQUEMAS_PERMITIDOS: [&str; 2] = ["http", "https"];

const MOTIVO_LOOPBACK: &str = "loopback";
const MOTIVO_LINK_LOCAL: &str = "link-local (inclui endereço de metadado de nuvem)";
const MOTIVO_PRIVADO: &str = "RFC1918 (rede privada) ou faixa não global reservada";
const MOTIVO_RESERVADO: &str = "endereço não global ou reservado/especial";
const MOTIVO_IP_INVALIDO: &str = "endereço IP inválido (bloqueado por segurança)";
const MOTIVO_USERINFO: &str = "URL com credenciais (userinfo) recusada";

/// Faixas IPv4 consideradas privadas/reservadas (lista do `ipaddress` do CPython 3.14).
const PRIVADAS_V4: [(Ipv4Addr, u32); 14] = [
    (Ipv4Addr::new(0, 0, 0, 0), 8),
    (Ipv4Addr::new(10, 0, 0, 0), 8),
    (Ipv4Addr::new(127, 0, 0, 0), 8),
    (Ipv4Addr::new(169, 254, 0, 0), 16),
    (Ipv4Addr::new(172, 16, 0, 0), 12),
    (Ipv4Addr::new(192, 0, 0, 0), 29),
    (Ipv4Addr::new(192, 0, 0, 170), 31),
    (Ipv4Addr::new(192, 0, 2, 0), 24),
    (Ipv4Addr::new(192, 168, 0, 0), 16),
    (Ipv4Addr::new(198, 18, 0, 0), 15),
    (Ipv4Addr::new(198, 51, 100, 0), 24),
    (Ipv4Addr::new(203, 0, 113, 0), 24),
    (Ipv4Addr::new(240, 0, 0, 0), 4),
    (Ipv4Addr::new(255, 255, 255, 255), 32),
];
/// Exceções globais dentro de 192.0.0.0/29 (CPython 3.14).
const GLOBAIS_EXCECAO_V4: [(Ipv4Addr, u32); 2] = [
    (Ipv4Addr::new(192, 0, 0, 9), 32),
    (Ipv4Addr::new(192, 0, 0, 10), 32),
];
/// Espaço de endereço compartilhado (CGNAT): não é global.
const COMPARTILHADO_V4: (Ipv4Addr, u32) = (Ipv4Addr::new(100, 64, 0, 0), 10);

/// Faixas IPv6 privadas (recorte dos prefixos principais do CPython 3.14).
const PRIVADAS_V6: [(Ipv6Addr, u32); 8] = [
    (Ipv6Addr::new(0, 0, 0, 0, 0, 0, 0, 0), 128),
    (Ipv6Addr::new(0x64, 0xff9b, 1, 0, 0, 0, 0, 0), 48),
    (Ipv6Addr::new(0x100, 0, 0, 0, 0, 0, 0, 0), 64),
    (Ipv6Addr::new(0x2001, 0, 0, 0, 0, 0, 0, 0), 23),
    (Ipv6Addr::new(0x2001, 0xdb8, 0, 0, 0, 0, 0, 0), 32),
    (Ipv6Addr::new(0x2002, 0, 0, 0, 0, 0, 0, 0), 16),
    (Ipv6Addr::new(0xfc00, 0, 0, 0, 0, 0, 0, 0), 7),
    (Ipv6Addr::new(0xfe80, 0, 0, 0, 0, 0, 0, 0), 10),
];
/// Exceções globais dentro de 2001::/23 (CPython 3.14).
const GLOBAIS_EXCECAO_V6: [(Ipv6Addr, u32); 6] = [
    (Ipv6Addr::new(0x2001, 1, 0, 0, 0, 0, 0, 1), 128),
    (Ipv6Addr::new(0x2001, 1, 0, 0, 0, 0, 0, 2), 128),
    (Ipv6Addr::new(0x2001, 3, 0, 0, 0, 0, 0, 0), 32),
    (Ipv6Addr::new(0x2001, 4, 0x112, 0, 0, 0, 0, 0), 48),
    (Ipv6Addr::new(0x2001, 0x20, 0, 0, 0, 0, 0, 0), 28),
    (Ipv6Addr::new(0x2001, 0x30, 0, 0, 0, 0, 0, 0), 28),
];

/// Motivo do bloqueio de um IP (literal, sem DNS), ou `None` se for global.
///
/// Mesmo critério de `_ip_bloqueado`. Aceita `fe80::1%eth0` (zona é descartada,
/// como em `_resolver_destino`).
pub fn classificar_ip(ip: &str) -> Option<&'static str> {
    let literal = ip.split('%').next().unwrap_or("");
    match literal.parse::<IpAddr>() {
        Ok(IpAddr::V4(v4)) => classificar_v4(v4),
        Ok(IpAddr::V6(v6)) => classificar_v6(v6),
        Err(_) => Some(MOTIVO_IP_INVALIDO),
    }
}

/// Checagem sintática de URL, sem DNS.
///
/// Recusa: esquema fora de http/https; qualquer `@` no netloc (userinfo);
/// URL sem host; porta inválida. Passar aqui não significa que o destino é
/// permitido: o chamador ainda precisa resolver o host e classificar os IPs.
pub fn validar_url(url: &str) -> Result<(), String> {
    destino(url).map(|_| ())
}

/// Host (minúsculo, sem colchetes) e porta de destino, sem resolver DNS.
///
/// A porta vem da URL ou do padrão do esquema (80 para http, 443 para https).
pub fn destino(url: &str) -> Result<(String, u16), String> {
    let limpa: String = url
        .chars()
        .filter(|c| !matches!(c, '\t' | '\r' | '\n'))
        .collect();
    let limpa = limpa.trim_matches(|c: char| c <= ' ');

    let (esquema, resto) = separar_esquema(limpa);
    let netloc = netloc_de(resto);

    // Igual ao urlsplit do Python: colchete desbalanceado já é URL malformada.
    if netloc.contains('[') != netloc.contains(']') {
        return Err("URL malformada: Invalid IPv6 URL".to_string());
    }
    if !ESQUEMAS_PERMITIDOS.contains(&esquema.as_str()) {
        return Err(format!("esquema '{esquema}' fora de ('http', 'https')"));
    }
    // Userinfo é recusado antes de qualquer host ou DNS: não pode sair no destino.
    if netloc.contains('@') {
        return Err(MOTIVO_USERINFO.to_string());
    }
    let (host, porta_txt) = host_e_porta(netloc);
    if host.is_empty() {
        return Err("sem host na URL".to_string());
    }

    let padrao: u16 = if esquema == "https" { 443 } else { 80 };
    let porta = match porta_txt {
        None | Some("") => padrao,
        Some(t) => {
            if !t.bytes().all(|b| b.is_ascii_digit()) {
                return Err(format!("porta inválida: '{t}'"));
            }
            match t.parse::<u32>() {
                Ok(n) if n <= 65535 => {
                    if n == 0 {
                        padrao
                    } else {
                        n as u16
                    }
                }
                _ => return Err(format!("porta inválida: '{t}' fora de 0-65535")),
            }
        }
    };
    Ok((host.to_ascii_lowercase(), porta))
}

fn classificar_v4(ip: Ipv4Addr) -> Option<&'static str> {
    if v4_global(ip) {
        return None;
    }
    if ip.is_loopback() {
        return Some(MOTIVO_LOOPBACK);
    }
    if ip.is_link_local() {
        return Some(MOTIVO_LINK_LOCAL);
    }
    if v4_privado(ip) {
        return Some(MOTIVO_PRIVADO);
    }
    Some(MOTIVO_RESERVADO)
}

fn classificar_v6(ip: Ipv6Addr) -> Option<&'static str> {
    // IPv4-mapeado (::ffff:a.b.c.d) é classificado pelo IPv4, como o Python 3.14.
    if let Some(v4) = ip.to_ipv4_mapped() {
        return classificar_v4(v4);
    }
    if ip == Ipv6Addr::LOCALHOST {
        return Some(MOTIVO_LOOPBACK);
    }
    if em_rede_v6(ip, Ipv6Addr::new(0xfe80, 0, 0, 0, 0, 0, 0, 0), 10) {
        return Some(MOTIVO_LINK_LOCAL);
    }
    if v6_global(ip) {
        return None;
    }
    if v6_privado(ip) {
        return Some(MOTIVO_PRIVADO);
    }
    Some(MOTIVO_RESERVADO)
}

fn v4_global(ip: Ipv4Addr) -> bool {
    if GLOBAIS_EXCECAO_V4.iter().any(|&(b, p)| em_rede_v4(ip, b, p)) {
        return true;
    }
    if em_rede_v4(ip, COMPARTILHADO_V4.0, COMPARTILHADO_V4.1) {
        return false;
    }
    !v4_privado(ip)
}

fn v4_privado(ip: Ipv4Addr) -> bool {
    PRIVADAS_V4.iter().any(|&(b, p)| em_rede_v4(ip, b, p))
}

fn v6_global(ip: Ipv6Addr) -> bool {
    !v6_privado(ip)
}

fn v6_privado(ip: Ipv6Addr) -> bool {
    if GLOBAIS_EXCECAO_V6.iter().any(|&(b, p)| em_rede_v6(ip, b, p)) {
        return false;
    }
    PRIVADAS_V6.iter().any(|&(b, p)| em_rede_v6(ip, b, p))
}

fn em_rede_v4(ip: Ipv4Addr, base: Ipv4Addr, prefixo: u32) -> bool {
    let mascara = u32::MAX.checked_shl(32 - prefixo).unwrap_or(0);
    (u32::from(ip) & mascara) == (u32::from(base) & mascara)
}

fn em_rede_v6(ip: Ipv6Addr, base: Ipv6Addr, prefixo: u32) -> bool {
    let mascara = u128::MAX.checked_shl(128 - prefixo).unwrap_or(0);
    (u128::from(ip) & mascara) == (u128::from(base) & mascara)
}

/// Separa o esquema (minúsculo) do resto. Sem esquema válido, devolve "".
fn separar_esquema(url: &str) -> (String, &str) {
    if let Some(i) = url.find(':') {
        let candidato = &url[..i];
        let primeiro_alfa = candidato
            .chars()
            .next()
            .is_some_and(|c| c.is_ascii_alphabetic());
        let caracteres_ok = candidato
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || matches!(c, '+' | '-' | '.'));
        if primeiro_alfa && caracteres_ok {
            return (candidato.to_ascii_lowercase(), &url[i + 1..]);
        }
    }
    (String::new(), url)
}

/// Netloc: o texto entre `//` e o primeiro `/`, `?` ou `#`.
fn netloc_de(resto: &str) -> &str {
    match resto.strip_prefix("//") {
        Some(r) => {
            let fim = r.find(['/', '?', '#']).unwrap_or(r.len());
            &r[..fim]
        }
        None => "",
    }
}

/// Divide o netloc (já sem userinfo) em host e texto da porta.
fn host_e_porta(netloc: &str) -> (&str, Option<&str>) {
    if let Some(i) = netloc.find('[') {
        let r = &netloc[i + 1..];
        return match r.find(']') {
            Some(f) => {
                let depois = &r[f + 1..];
                (&r[..f], depois.split_once(':').map(|(_, p)| p))
            }
            None => (r, None),
        };
    }
    match netloc.split_once(':') {
        Some((h, p)) => (h, Some(p)),
        None => (netloc, None),
    }
}
