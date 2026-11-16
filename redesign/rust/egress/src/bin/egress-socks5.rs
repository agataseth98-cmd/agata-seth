//! SOCKS5 local de saída em loopback. Imprime `socks5://127.0.0.1:<porta>` na
//! primeira linha e atende até ser encerrado. Uso: egress-socks5 [porta] (0 = livre).
use egress::socks5::{atender, conectar_validado};
use std::io::Write;
use std::net::TcpListener;
use std::thread;

fn main() {
    let porta: u16 = std::env::args().nth(1).and_then(|p| p.parse().ok()).unwrap_or(0);
    let ouvinte = TcpListener::bind(("127.0.0.1", porta)).expect("bind 127.0.0.1");
    println!("socks5://{}", ouvinte.local_addr().expect("endereço local"));
    let _ = std::io::stdout().flush();
    for c in ouvinte.incoming().flatten() {
        thread::spawn(move || {
            let _ = atender(c, conectar_validado);
        });
    }
}
