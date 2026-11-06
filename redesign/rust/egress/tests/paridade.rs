//! Paridade com `redesign/alexandria/tests/test_egress_userinfo.py` e com os
//! casos de classificação de IP de `scripts/politica_egress.py`.
//!
//! Os casos extras (IPs e esquemas) têm o veredito conferido contra o Python
//! 3.14 (`politica_egress._ip_bloqueado` e `_resolver_destino`) na mesma data.

use egress::{classificar_ip, destino, validar_url};

const MSG_USERINFO: &str = "URL com credenciais (userinfo) recusada";
const MOTIVO_LINK_LOCAL: &str = "link-local (inclui endereço de metadado de nuvem)";
const MOTIVO_PRIVADO: &str = "RFC1918 (rede privada) ou faixa não global reservada";
const MOTIVO_RESERVADO: &str = "endereço não global ou reservado/especial";

// --- test_egress_userinfo.py ---

#[test]
fn url_com_usuario_e_senha_e_recusada() {
    // Python: test_url_com_usuario_e_senha_e_recusada_antes_do_dns
    assert_eq!(
        validar_url("https://user:senha@exemplo.invalid/p"),
        Err(MSG_USERINFO.to_string())
    );
}

#[test]
fn url_so_com_usuario_tambem_e_recusada() {
    // Python: test_url_so_com_usuario_tambem_e_recusada_antes_do_dns
    assert_eq!(
        validar_url("https://token@exemplo.invalid/"),
        Err(MSG_USERINFO.to_string())
    );
}

#[test]
fn url_sem_userinfo_passa_na_checagem_de_userinfo() {
    // Python: test_url_sem_userinfo_segue_para_o_dns. Aqui não há DNS: a
    // checagem sintática passa e o host vai para o chamador resolver.
    assert_eq!(validar_url("https://exemplo.invalid/p"), Ok(()));
    assert_eq!(
        destino("https://exemplo.invalid/p"),
        Ok(("exemplo.invalid".to_string(), 443))
    );
}

// --- classificação de IP (casos da lista do selftest / pedido) ---

#[test]
fn loopback_127_0_0_1() {
    assert_eq!(classificar_ip("127.0.0.1"), Some("loopback"));
}

#[test]
fn link_local_metadado_nuvem() {
    assert_eq!(classificar_ip("169.254.169.254"), Some(MOTIVO_LINK_LOCAL));
}

#[test]
fn privado_10_0_0_1() {
    assert_eq!(classificar_ip("10.0.0.1"), Some(MOTIVO_PRIVADO));
}

#[test]
fn global_8_8_8_8() {
    assert_eq!(classificar_ip("8.8.8.8"), None);
}

// --- classificação de IP, casos extras medidos no Python 3.14 ---

#[test]
fn ipv4_extras_iguais_ao_python() {
    let casos: [(&str, Option<&str>); 13] = [
        ("0.0.0.0", Some(MOTIVO_PRIVADO)),
        ("100.64.0.1", Some(MOTIVO_RESERVADO)),
        ("172.16.0.1", Some(MOTIVO_PRIVADO)),
        ("172.32.0.1", None),
        ("192.168.1.1", Some(MOTIVO_PRIVADO)),
        ("224.0.0.1", None),
        ("255.255.255.255", Some(MOTIVO_PRIVADO)),
        ("192.0.0.9", None),
        ("198.18.0.1", Some(MOTIVO_PRIVADO)),
        ("240.0.0.1", Some(MOTIVO_PRIVADO)),
        ("1.1.1.1", None),
        ("203.0.113.5", Some(MOTIVO_PRIVADO)),
        ("169.254.0.1", Some(MOTIVO_LINK_LOCAL)),
    ];
    for (ip, esperado) in casos {
        assert_eq!(classificar_ip(ip), esperado, "IPv4 {ip}");
    }
}

#[test]
fn ipv6_extras_iguais_ao_python() {
    let casos: [(&str, Option<&str>); 16] = [
        ("::1", Some("loopback")),
        ("fe80::1", Some(MOTIVO_LINK_LOCAL)),
        ("fc00::1", Some(MOTIVO_PRIVADO)),
        ("2001:db8::1", Some(MOTIVO_PRIVADO)),
        ("2606:4700::1111", None),
        ("::ffff:127.0.0.1", Some("loopback")),
        ("::ffff:10.0.0.1", Some(MOTIVO_PRIVADO)),
        ("::ffff:8.8.8.8", None),
        ("2002::1", Some(MOTIVO_PRIVADO)),
        ("64:ff9b:1::1", Some(MOTIVO_PRIVADO)),
        ("64:ff9b::808:808", None),
        ("2001:1::1", None),
        ("2001:20::1", None),
        ("2001:0:4136:e378::1", Some(MOTIVO_PRIVADO)),
        ("100::1", Some(MOTIVO_PRIVADO)),
        ("::", Some(MOTIVO_PRIVADO)),
    ];
    for (ip, esperado) in casos {
        assert_eq!(classificar_ip(ip), esperado, "IPv6 {ip}");
    }
}

#[test]
fn zona_ipv6_e_descartada_como_no_python() {
    assert_eq!(classificar_ip("fe80::1%eth0"), Some(MOTIVO_LINK_LOCAL));
}

#[test]
fn ip_invalido_fica_bloqueado() {
    // Divergência deliberada: o Python levantaria ValueError; aqui é fail-closed.
    assert!(classificar_ip("nao-e-ip").is_some());
    assert!(classificar_ip("010.0.0.1").is_some());
}

// --- esquema, host e porta (casos de _selftest do Python) ---

#[test]
fn esquema_fora_de_http_https_e_recusado() {
    // Python: ftp://example.com/ e file:///etc/passwd -> permitido=False
    assert_eq!(
        validar_url("ftp://example.com/"),
        Err("esquema 'ftp' fora de ('http', 'https')".to_string())
    );
    assert_eq!(
        validar_url("file:///etc/passwd"),
        Err("esquema 'file' fora de ('http', 'https')".to_string())
    );
}

#[test]
fn https_publico_passa_na_sintaxe() {
    // Python: https://example.com/ -> permitido=True (com DNS). Aqui só a sintaxe.
    assert_eq!(validar_url("https://example.com/"), Ok(()));
}

#[test]
fn url_sem_host_e_recusada() {
    assert_eq!(validar_url("http:///caminho"), Err("sem host na URL".to_string()));
    assert_eq!(validar_url("https://:443/"), Err("sem host na URL".to_string()));
}

#[test]
fn porta_padrao_e_porta_explicita() {
    assert_eq!(destino("http://exemplo.invalid/"), Ok(("exemplo.invalid".to_string(), 80)));
    assert_eq!(destino("https://exemplo.invalid/"), Ok(("exemplo.invalid".to_string(), 443)));
    assert_eq!(
        destino("http://127.0.0.1:20126/"),
        Ok(("127.0.0.1".to_string(), 20126))
    );
}

#[test]
fn porta_fora_de_faixa_e_recusada() {
    assert!(validar_url("http://exemplo.invalid:99999/")
        .unwrap_err()
        .starts_with("porta inválida"));
    assert!(validar_url("http://exemplo.invalid:abc/")
        .unwrap_err()
        .starts_with("porta inválida"));
}

#[test]
fn ipv6_literal_no_host_sem_colchetes() {
    assert_eq!(destino("http://[::1]:8080/"), Ok(("::1".to_string(), 8080)));
}

#[test]
fn colchete_desbalanceado_e_malformada() {
    assert!(validar_url("http://[::1/").unwrap_err().starts_with("URL malformada"));
}

#[test]
fn userinfo_vence_a_checagem_de_host() {
    // Userinfo é recusado antes de qualquer checagem de host ou porta.
    assert_eq!(
        validar_url("https://user@:443/"),
        Err(MSG_USERINFO.to_string())
    );
}
