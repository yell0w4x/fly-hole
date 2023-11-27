use tiny_http::{Server, Response, Request, Method, Header};
use http::Uri;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::vec::Vec;
use ctrlc;
use std::collections::HashMap;
use querystring::querify;
use base64::{Engine as _, engine::general_purpose};
use std::net::UdpSocket;
use std::time::Duration;
use std::error::Error;
use simple_error::bail;


fn dns_relay(dns_req: &Vec<u8>) -> Result<Vec<u8>, Box<dyn Error>>  {
    const DNS_ENDPOINT: &str = "127.0.0.1:53";

    let socket = UdpSocket::bind("0.0.0.0:0")?;
    socket.set_read_timeout(Some(Duration::new(5, 0)))?;
    socket.send_to(dns_req, DNS_ENDPOINT)?;

    const MAX_DATAGRAM_SIZE: usize = 65_507;
    let mut buf = vec![0u8; MAX_DATAGRAM_SIZE];
    let (len, _) = socket.recv_from(&mut buf)?;
    let dns_resp = &mut buf[..len];

    return Ok(dns_resp.to_vec());
}


const DNS_MESSAGE_TYPE: &str = "application/dns-message";
const CONTENT_TYPE: &str = "content-type";


fn handle_dns(dns_req: &Vec<u8>, req: Request) {
    let dns_resp: Vec<u8> = match dns_relay(&dns_req) {
        Ok(dns_resp) => dns_resp,
        Err(_e) => { 
            let _ = req.respond(Response::empty(502));
            return;
        }
    };

    println!("dns_req: {:?}, dns_resp: {:?}", dns_req, dns_resp);
    let mut resp = Response::from_data(dns_resp);
    resp.add_header(Header::from_bytes(CONTENT_TYPE.as_bytes(), DNS_MESSAGE_TYPE.as_bytes()).unwrap());
    let _ = req.respond(resp);
}

fn check_content_type(req: &Request) -> Result<(), Box<dyn Error>> {
    let headers_list = req.headers();
    let mut headers: HashMap<String, String> = HashMap::new();
    for header in headers_list {
        headers.insert(header.field.as_str().as_str().to_ascii_lowercase(), 
            header.value.as_str().to_ascii_lowercase());
    }

    if ! headers.contains_key(CONTENT_TYPE) || headers.get(CONTENT_TYPE).unwrap() != DNS_MESSAGE_TYPE {
        bail!("Bad request: No content-type header")
    } else {
        Ok(())
    }
} 


fn handle_get(uri: &Uri, req: Request) {
    if uri.query().is_none() {
        let _ = req.respond(Response::empty(400));
        return;
    }

    let vars_vec = querify(uri.query().unwrap());
    let vars: HashMap<_, _> = vars_vec.into_iter().collect();
    if !vars.contains_key("dns") {
        let _ = req.respond(Response::empty(400));
        return;
    } 

    let dns_req_b64 = vars.get("dns").unwrap();
    if dns_req_b64.len() == 0 {
        let _ = req.respond(Response::empty(400));
        return;
    }

    let dns_req = match general_purpose::STANDARD_NO_PAD.decode(
        vars.get("dns").unwrap()) {
            Ok(dns_req) => dns_req,
            Err(_e) => {
                let _ = req.respond(Response::empty(400));
                return;
            }
        };
    handle_dns(&dns_req, req);
}


fn handle_post(mut req: Request) {
    if check_content_type(&req).is_err() {
        let _ = req.respond(Response::empty(400));
        return;
    }

    if req.body_length() == Some(0) {
        let _ = req.respond(Response::empty(400));
        return;
    }

    const MAX_DATAGRAM_SIZE: usize = 65_507;
    let mut buf:[u8; MAX_DATAGRAM_SIZE] = [0; MAX_DATAGRAM_SIZE];
    let len = match req.as_reader().read(&mut buf) {
        Ok(len) => len,
        Err(_e) => {
            let _ = req.respond(Response::empty(400));
            return;
        }
    };

    let dns_req = &buf[..len].to_vec();
    handle_dns(&dns_req, req);
}


fn handle_root(uri: &Uri, req: Request) {
    println!("URL: {}", req.url());

    if req.method() == &Method::Get {
        handle_get(uri, req);
    } else if req.method() == &Method::Post {
        handle_post(req);
    } else {
        let _ = req.respond(Response::empty(405));
    }
}


fn handle_rest(req: Request) {
    let _ = req.respond(Response::empty(404));
}


fn wait_for_sigint() {
    let running = Arc::new(AtomicBool::new(true));
    let r = running.clone();

    ctrlc::set_handler(move || {
        r.store(false, Ordering::SeqCst);
    }).expect("Error setting Ctrl-C handler");

    println!("Ctrl-C to quit");
    while running.load(Ordering::SeqCst) {
        thread::sleep(Duration::from_millis(100));
    }
    println!("Exiting...");    
}


fn main() {
    const ENDPOINT: &str = "0.0.0.0:8000";
    let server = Server::http(ENDPOINT).unwrap();
    println!("Listening on {}...", ENDPOINT);

    let server = Arc::new(server);
    let mut guards = Vec::with_capacity(4);
    
    for i in 0 .. num_cpus::get() {
        println!("Spawning {}", i);
        let server = server.clone();
        let guard = thread::spawn(move || {
            loop {
                let req = match server.recv() {
                    Ok(rq) => rq,
                    Err(e) => { println!("An error: {}", e); break }
                };

                let uri = req.url().parse::<Uri>().unwrap();
                match uri.path() {
                    "/" => { handle_root(&uri, req); }
                    &_ => { handle_rest(req); }
                }
            }
        });
    
        guards.push(guard);
    }

    wait_for_sigint();
}
