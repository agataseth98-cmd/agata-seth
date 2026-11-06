//! CLI mínima da camada Rust de egress.
//!
//! Uso:
//!   egress ip <endereco>   -> "global" (exit 0) ou "bloqueado: <motivo>" (exit 1)
//!   egress url <url>       -> host e porta (exit 0) ou "bloqueado: <motivo>" (exit 1)
//!
//! Não faz DNS: só classifica o literal de IP e a sintaxe da URL.

use egress::{classificar_ip, destino};
use std::process::ExitCode;

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    match args.iter().map(String::as_str).collect::<Vec<_>>().as_slice() {
        ["ip", ip] => match classificar_ip(ip) {
            None => {
                println!("global");
                ExitCode::SUCCESS
            }
            Some(motivo) => {
                println!("bloqueado: {motivo}");
                ExitCode::from(1)
            }
        },
        ["url", url] => match destino(url) {
            Ok((host, porta)) => {
                println!("sintaxe ok: host={host} porta={porta} (DNS e IPs ficam fora desta camada)");
                ExitCode::SUCCESS
            }
            Err(motivo) => {
                println!("bloqueado: {motivo}");
                ExitCode::from(1)
            }
        },
        _ => {
            eprintln!("uso: egress ip <endereco> | egress url <url>");
            ExitCode::from(2)
        }
    }
}
