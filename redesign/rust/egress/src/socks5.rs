//! SOCKS5 local de saída (D6, decisão do Humano, 15/11/2026): espelho de
//! `redesign/mcp/navegador/egress_proxy.py`. Só CONNECT, sem autenticação.
//! Resolve o destino uma vez, recusa se QUALQUER IP não for global
//! (`classificar_ip`) e conecta ao literal validado, sem nova resolução.

use crate::classificar_ip;
use std::io::{self, Read, Write};
use std::net::{Ipv4Addr, Ipv6Addr, Shutdown, SocketAddr, TcpStream, ToSocketAddrs};
use std::thread;
use std::time::Duration;

/// Falha ao conectar: `Bloqueado` vira status SOCKS 2; `Rede`, status 5.
#[derive(Debug)]
pub enum Falha {
    Bloqueado(String),
    Rede(String),
}

/// Endereços do destino, todos validados; erro se algum não for global.
pub fn enderecos_publicos(host: &str, porta: u16) -> Result<Vec<SocketAddr>, Falha> {
    let addrs: Vec<SocketAddr> = (host, porta)
        .to_socket_addrs()
        .map_err(|e| Falha::Rede(format!("DNS: {e}")))?
        .collect();
    if addrs.is_empty() {
        return Err(Falha::Rede("DNS não devolveu endereços".into()));
    }
    for a in &addrs {
        if let Some(motivo) = classificar_ip(&a.ip().to_string()) {
            return Err(Falha::Bloqueado(format!("destino bloqueado: {} ({motivo})", a.ip())));
        }
    }
    Ok(addrs)
}

/// Conexão de produção: valida e conecta ao IP literal validado.
pub fn conectar_validado(host: &str, porta: u16) -> Result<TcpStream, Falha> {
    let mut erro = String::new();
    for a in enderecos_publicos(host, porta)? {
        match TcpStream::connect_timeout(&a, Duration::from_secs(15)) {
            Ok(s) => return Ok(s),
            Err(e) => erro = e.to_string(),
        }
    }
    Err(Falha::Rede(format!("nenhum IP validado aceitou conexão: {erro}")))
}

fn ler(s: &mut TcpStream, n: usize) -> io::Result<Vec<u8>> {
    let mut b = vec![0u8; n];
    s.read_exact(&mut b)?;
    Ok(b)
}

fn responder(s: &mut TcpStream, status: u8) -> io::Result<()> {
    s.write_all(&[5, status, 0, 1, 0, 0, 0, 0, 0, 0])
}

/// Atende um cliente. `conectar` é injetável para teste.
pub fn atender<F>(mut cliente: TcpStream, conectar: F) -> io::Result<()>
where
    F: Fn(&str, u16) -> Result<TcpStream, Falha>,
{
    cliente.set_read_timeout(Some(Duration::from_secs(30)))?;
    let cab = ler(&mut cliente, 2)?;
    let metodos = ler(&mut cliente, cab[1] as usize)?;
    if cab[0] != 5 || !metodos.contains(&0) {
        return cliente.write_all(&[5, 0xff]);
    }
    cliente.write_all(&[5, 0])?;
    let req = ler(&mut cliente, 4)?;
    if req[0] != 5 || req[1] != 1 {
        return responder(&mut cliente, 7);
    }
    let host = match req[3] {
        1 => {
            let b = ler(&mut cliente, 4)?;
            Ipv4Addr::new(b[0], b[1], b[2], b[3]).to_string()
        }
        4 => {
            let b = ler(&mut cliente, 16)?;
            let mut a = [0u8; 16];
            a.copy_from_slice(&b);
            Ipv6Addr::from(a).to_string()
        }
        3 => {
            let n = ler(&mut cliente, 1)?[0] as usize;
            match String::from_utf8(ler(&mut cliente, n)?) {
                Ok(h) if h.is_ascii() => h,
                _ => return responder(&mut cliente, 1),
            }
        }
        _ => return responder(&mut cliente, 8),
    };
    let p = ler(&mut cliente, 2)?;
    let porta = u16::from_be_bytes([p[0], p[1]]);
    let remoto = match conectar(&host, porta) {
        Ok(r) => r,
        Err(Falha::Bloqueado(_)) => return responder(&mut cliente, 2),
        Err(Falha::Rede(_)) => return responder(&mut cliente, 5),
    };
    responder(&mut cliente, 0)?;
    cliente.set_read_timeout(None)?;
    retransmitir(cliente, remoto)
}

fn retransmitir(a: TcpStream, b: TcpStream) -> io::Result<()> {
    let (mut a2, mut b2) = (a.try_clone()?, b.try_clone()?);
    let ida = thread::spawn(move || {
        let mut a = a;
        let mut b = b;
        let _ = io::copy(&mut a, &mut b);
        let _ = b.shutdown(Shutdown::Write);
    });
    let _ = io::copy(&mut b2, &mut a2);
    let _ = a2.shutdown(Shutdown::Write);
    let _ = ida.join();
    Ok(())
}
