use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::thread;
use std::time::Instant;
use serde::{Deserialize, Serialize};

// ─── Mathematical Similarity Engine ──────────────────────────────────────────

pub fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    if a.len() != b.len() || a.is_empty() {
        return 0.0;
    }
    let mut dot = 0.0f32;
    let mut norm_a = 0.0f32;
    let mut norm_b = 0.0f32;

    for i in 0..a.len() {
        dot += a[i] * b[i];
        norm_a += a[i] * a[i];
        norm_b += b[i] * b[i];
    }

    let denom = norm_a.sqrt() * norm_b.sqrt();
    if denom == 0.0 {
        0.0
    } else {
        dot / denom
    }
}

// ─── Data Contracts ──────────────────────────────────────────────────────────

#[derive(Deserialize)]
struct SimilarityRequest {
    vector_a: Vec<f32>,
    vector_b: Vec<f32>,
}

#[derive(Serialize)]
struct SimilarityResponse {
    similarity: f32,
    dimension: usize,
    calculation_time_ns: u128,
}

#[derive(Deserialize, Clone)]
struct AnimeCandidate {
    id: String,
    title: String,
    genre: String,
    vector: Vec<f32>,
}

#[derive(Deserialize)]
struct RankRequest {
    user_vector: Vec<f32>,
    candidates: Vec<AnimeCandidate>,
    top_k: Option<usize>,
}

#[derive(Serialize)]
struct RankedItem {
    id: String,
    title: String,
    genre: String,
    score: f32,
}

#[derive(Serialize)]
struct RankResponse {
    top_k: usize,
    latency_us: u128,
    results: Vec<RankedItem>,
}

#[derive(Serialize)]
struct HealthResponse {
    status: String,
    service: String,
    engine: String,
}

// ─── HTTP Connection Handler ─────────────────────────────────────────────────

fn handle_client(mut stream: TcpStream) {
    let mut buffer = [0; 65536];
    let bytes_read = match stream.read(&mut buffer) {
        Ok(n) if n > 0 => n,
        _ => return,
    };

    let req_str = match std::str::from_utf8(&buffer[..bytes_read]) {
        Ok(s) => s,
        Err(_) => return,
    };

    let mut lines = req_str.lines();
    let request_line = match lines.next() {
        Some(line) => line,
        None => return,
    };

    let parts: Vec<&str> = request_line.split_whitespace().collect();
    if parts.len() < 2 {
        return;
    }
    let method = parts[0];
    let path = parts[1];

    // CORS pre-flight
    if method == "OPTIONS" {
        let resp = "HTTP/1.1 200 OK\r\n\
                    Access-Control-Allow-Origin: *\r\n\
                    Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n\
                    Access-Control-Allow-Headers: Content-Type\r\n\
                    Content-Length: 0\r\n\r\n";
        let _ = stream.write_all(resp.as_bytes());
        return;
    }

    // Extract JSON Body
    let body = req_str.split("\r\n\r\n").nth(1).unwrap_or("");

    if path == "/health" || path == "/api/v1/score/health" {
        let health = HealthResponse {
            status: "healthy".to_string(),
            service: "rust-scoring-engine".to_string(),
            engine: "native-simd-cosine".to_string(),
        };
        send_json_response(&mut stream, 200, &health);
        return;
    }

    if method == "POST" && path == "/api/v1/score/similarity" {
        let start = Instant::now();
        match serde_json::from_str::<SimilarityRequest>(body) {
            Ok(req) => {
                let sim = cosine_similarity(&req.vector_a, &req.vector_b);
                let duration = start.elapsed().as_nanos();
                let resp = SimilarityResponse {
                    similarity: (sim * 10000.0).round() / 10000.0,
                    dimension: req.vector_a.len(),
                    calculation_time_ns: duration,
                };
                send_json_response(&mut stream, 200, &resp);
            }
            Err(e) => {
                send_error_response(&mut stream, 400, &format!("Invalid JSON: {}", e));
            }
        }
        return;
    }

    if method == "POST" && path == "/api/v1/score/rank" {
        let start = Instant::now();
        match serde_json::from_str::<RankRequest>(body) {
            Ok(req) => {
                let top_k = req.top_k.unwrap_or(10);
                let mut scored: Vec<RankedItem> = req.candidates.into_iter().map(|c| {
                    let sim = cosine_similarity(&req.user_vector, &c.vector);
                    RankedItem {
                        id: c.id,
                        title: c.title,
                        genre: c.genre,
                        score: (sim * 10000.0).round() / 10000.0,
                    }
                }).collect();

                // Sort descending by score
                scored.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
                scored.truncate(top_k);

                let latency_us = start.elapsed().as_micros();
                let resp = RankResponse {
                    top_k: scored.len(),
                    latency_us,
                    results: scored,
                };
                send_json_response(&mut stream, 200, &resp);
            }
            Err(e) => {
                send_error_response(&mut stream, 400, &format!("Invalid JSON: {}", e));
            }
        }
        return;
    }

    send_error_response(&mut stream, 404, "Endpoint not found");
}

fn send_json_response<T: Serialize>(stream: &mut TcpStream, status_code: u16, data: &T) {
    let json_bytes = serde_json::to_vec(data).unwrap_or_default();
    let header = format!(
        "HTTP/1.1 {} OK\r\n\
         Content-Type: application/json\r\n\
         Access-Control-Allow-Origin: *\r\n\
         Content-Length: {}\r\n\
         Connection: close\r\n\r\n",
        status_code,
        json_bytes.len()
    );
    let _ = stream.write_all(header.as_bytes());
    let _ = stream.write_all(&json_bytes);
}

fn send_error_response(stream: &mut TcpStream, status_code: u16, msg: &str) {
    let err_json = format!("{{\"error\":\"{}\"}}", msg);
    let header = format!(
        "HTTP/1.1 {} ERROR\r\n\
         Content-Type: application/json\r\n\
         Access-Control-Allow-Origin: *\r\n\
         Content-Length: {}\r\n\
         Connection: close\r\n\r\n",
        status_code,
        err_json.len()
    );
    let _ = stream.write_all(header.as_bytes());
    let _ = stream.write_all(err_json.as_bytes());
}

fn main() {
    let port = std::env::var("PORT").unwrap_or_else(|_| "8083".to_string());
    let addr = format!("0.0.0.0:{}", port);
    let listener = TcpListener::bind(&addr).expect("Failed to bind to address");
    println!("[✓] Rust Scoring Engine microservice listening on :{}", port);

    for stream in listener.incoming() {
        match stream {
            Ok(s) => {
                thread::spawn(move || handle_client(s));
            }
            Err(e) => eprintln!("Connection failed: {}", e),
        }
    }
}

// ─── Unit Tests ──────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cosine_similarity_identical() {
        let v1 = vec![1.0, 2.0, 3.0];
        let v2 = vec![1.0, 2.0, 3.0];
        let sim = cosine_similarity(&v1, &v2);
        assert!((sim - 1.0).abs() < 1e-4);
    }

    #[test]
    fn test_cosine_similarity_orthogonal() {
        let v1 = vec![1.0, 0.0];
        let v2 = vec![0.0, 1.0];
        let sim = cosine_similarity(&v1, &v2);
        assert!((sim - 0.0).abs() < 1e-4);
    }

    #[test]
    fn test_cosine_similarity_opposite() {
        let v1 = vec![1.0, 1.0];
        let v2 = vec![-1.0, -1.0];
        let sim = cosine_similarity(&v1, &v2);
        assert!((sim - (-1.0)).abs() < 1e-4);
    }
}
