//! Testes da camada 2 (DNS, redirect, pinagem). Sem internet: só `localhost`
//! e IPs literais; o host sem resolução é recusado pela sintaxe, antes do DNS.

use egress::camada2::{
    resolver_e_classificar, seguir_redirects, validar_redirect, validar_redirect_com_ips,
    LIMITE_REDIRECTS,
};
use std::net::IpAddr;

const ORIGEM: &str = "http://8.8.8.8/a/b";

fn locations(n: usize) -> Vec<String> {
    (1..=n).map(|i| format!("/p{i}")).collect()
}

#[test]
fn localhost_resolve_e_e_recusado_como_loopback() {
    let erro = resolver_e_classificar("localhost", 80).expect_err("localhost deve ser recusado");
    assert!(erro.contains("loopback"), "{erro}");
}

#[test]
fn ip_literal_publico_e_devolvido_para_pinagem() {
    let ips = resolver_e_classificar("8.8.8.8", 443).unwrap();
    assert_eq!(ips, vec!["8.8.8.8".parse::<IpAddr>().unwrap()]);
}

#[test]
fn ip_literal_privado_e_recusado() {
    let erro = resolver_e_classificar("10.0.0.1", 80).expect_err("RFC1918 deve ser recusado");
    assert!(erro.contains("RFC1918"), "{erro}");
}

#[test]
fn host_sem_resolucao_e_recusado() {
    assert!(resolver_e_classificar("", 80).is_err());
    assert!(resolver_e_classificar("nao resolve", 80).is_err());
    assert!(resolver_e_classificar("fe80::1%eth0", 80).is_err());
}

#[test]
fn location_relativo_valido_resolve_sobre_a_origem() {
    assert_eq!(validar_redirect(ORIGEM, "c").unwrap(), "http://8.8.8.8/a/c");
    assert_eq!(validar_redirect(ORIGEM, "/x?y=1").unwrap(), "http://8.8.8.8/x?y=1");
    assert_eq!(validar_redirect(ORIGEM, "../d/").unwrap(), "http://8.8.8.8/d/");
    assert_eq!(
        validar_redirect("https://8.8.8.8/a/b?q=1", "?z=2").unwrap(),
        "https://8.8.8.8/a/b?z=2"
    );
}

#[test]
fn location_relativo_devolve_o_ip_pinado() {
    let (url, ips) = validar_redirect_com_ips(ORIGEM, "/x").unwrap();
    assert_eq!(url, "http://8.8.8.8/x");
    assert_eq!(ips, vec!["8.8.8.8".parse::<IpAddr>().unwrap()]);
}

#[test]
fn location_que_vira_userinfo_e_recusado() {
    let e1 = validar_redirect(ORIGEM, "http://user:senha@8.8.8.8/").unwrap_err();
    assert!(e1.contains("userinfo"), "{e1}");
    let e2 = validar_redirect(ORIGEM, "//atacante@8.8.8.8/").unwrap_err();
    assert!(e2.contains("userinfo"), "{e2}");
}

#[test]
fn location_com_esquema_ftp_e_recusado() {
    let erro = validar_redirect(ORIGEM, "ftp://8.8.8.8/arquivo").unwrap_err();
    assert!(erro.contains("esquema"), "{erro}");
}

#[test]
fn location_para_ip_ou_host_bloqueado_e_recusado() {
    assert!(validar_redirect(ORIGEM, "http://127.0.0.1/").unwrap_err().contains("loopback"));
    assert!(validar_redirect(ORIGEM, "http://localhost/").unwrap_err().contains("loopback"));
    assert!(validar_redirect(ORIGEM, "http://169.254.169.254/latest/")
        .unwrap_err()
        .contains("link-local"));
}

#[test]
fn location_com_barra_invertida_nao_muda_o_host() {
    assert!(validar_redirect(ORIGEM, "http:\\\\localhost\\x").is_err());
    assert_eq!(
        validar_redirect(ORIGEM, "/\\evil.example").unwrap(),
        "http://8.8.8.8/\\evil.example"
    );
}

#[test]
fn limite_de_redirects_e_dez() {
    assert_eq!(LIMITE_REDIRECTS, 10);
    let v = locations(10);
    let refs: Vec<&str> = v.iter().map(String::as_str).collect();
    assert_eq!(seguir_redirects(ORIGEM, &refs).unwrap(), "http://8.8.8.8/p10");
}

#[test]
fn onze_redirects_sao_recusados() {
    let v = locations(11);
    let refs: Vec<&str> = v.iter().map(String::as_str).collect();
    let erro = seguir_redirects(ORIGEM, &refs).unwrap_err();
    assert!(erro.contains("limite"), "{erro}");
}

#[test]
fn cadeia_com_salto_para_loopback_e_recusada() {
    let erro = seguir_redirects(ORIGEM, &["/ok", "http://127.0.0.1/", "/depois"]).unwrap_err();
    assert!(erro.contains("loopback"), "{erro}");
}

#[test]
fn seguir_redirects_com_ips_devolve_ip_pinado_por_salto() {
    use egress::camada2::seguir_redirects_com_ips;
    let saltos = seguir_redirects_com_ips("https://8.8.8.8/a", &["/b", "/c"]).expect("deve passar");
    assert_eq!(saltos.len(), 3, "inicial + 2 redirects");
    for (_url, ips) in &saltos {
        assert!(!ips.is_empty(), "cada salto precisa de IP pinado");
    }
    assert_eq!(saltos[2].0, "https://8.8.8.8/c");
}

#[test]
fn seguir_redirects_com_ips_recusa_salto_para_loopback() {
    use egress::camada2::seguir_redirects_com_ips;
    let r = seguir_redirects_com_ips("https://8.8.8.8/a", &["https://127.0.0.1/x"]);
    assert!(r.is_err(), "salto para loopback deve ser recusado");
}
