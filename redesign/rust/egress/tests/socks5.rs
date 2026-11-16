//! Paridade com scripts/testar_egress_proxy.py (casos do SOCKS5 em Python).
use egress::socks5::{atender, enderecos_publicos, Falha};
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::thread;

#[test]
fn recusa_loopback_literal() {
    assert!(matches!(enderecos_publicos("127.0.0.1", 443), Err(Falha::Bloqueado(_))));
}

#[test]
fn recusa_nat_de_operadora() {
    assert!(matches!(enderecos_publicos("100.64.0.1", 443), Err(Falha::Bloqueado(_))));
}

#[test]
fn aceita_ip_global_literal() {
    let v = enderecos_publicos("1.1.1.1", 443).map_err(|_| ()).unwrap();
    assert_eq!(v[0].to_string(), "1.1.1.1:443");
}

fn par() -> (TcpStream, TcpStream) {
    let l = TcpListener::bind("127.0.0.1:0").unwrap();
    let c = TcpStream::connect(l.local_addr().unwrap()).unwrap();
    (c, l.accept().unwrap().0)
}

#[test]
fn tunela_so_depois_de_validar() {
    let eco = TcpListener::bind("127.0.0.1:0").unwrap();
    let porta_eco = eco.local_addr().unwrap().port();
    thread::spawn(move || {
        let (mut s, _) = eco.accept().unwrap();
        let mut b = [0u8; 4];
        s.read_exact(&mut b).unwrap();
        s.write_all(&b).unwrap();
    });
    let (mut cliente, servidor) = par();
    let h = thread::spawn(move || {
        atender(servidor, move |host, p| {
            assert_eq!((host, p), ("allowed.example", porta_eco));
            TcpStream::connect(("127.0.0.1", porta_eco)).map_err(|e| Falha::Rede(e.to_string()))
        })
    });
    cliente.write_all(&[5, 1, 0]).unwrap();
    let mut r = [0u8; 2];
    cliente.read_exact(&mut r).unwrap();
    assert_eq!(r, [5, 0]);
    let host = b"allowed.example";
    let mut req = vec![5, 1, 0, 3, host.len() as u8];
    req.extend_from_slice(host);
    req.extend_from_slice(&porta_eco.to_be_bytes());
    cliente.write_all(&req).unwrap();
    let mut resp = [0u8; 10];
    cliente.read_exact(&mut resp).unwrap();
    assert_eq!(&resp[..2], &[5, 0]);
    cliente.write_all(b"test").unwrap();
    let mut eco_b = [0u8; 4];
    cliente.read_exact(&mut eco_b).unwrap();
    assert_eq!(&eco_b, b"test");
    drop(cliente);
    h.join().unwrap().unwrap();
}

#[test]
fn bloqueio_vira_status_2_sem_conectar() {
    let (mut cliente, servidor) = par();
    let h = thread::spawn(move || {
        atender(servidor, |_, _| Err(Falha::Bloqueado("teste".into())))
    });
    cliente.write_all(&[5, 1, 0]).unwrap();
    let mut r = [0u8; 2];
    cliente.read_exact(&mut r).unwrap();
    cliente.write_all(&[5, 1, 0, 1, 127, 0, 0, 1, 0, 80]).unwrap();
    let mut resp = [0u8; 10];
    cliente.read_exact(&mut resp).unwrap();
    assert_eq!(resp[1], 2);
    h.join().unwrap().unwrap();
}
