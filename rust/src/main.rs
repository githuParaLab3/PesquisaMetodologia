use actix_web::{get, web, App, HttpResponse, HttpServer};
use rand::Rng;
use serde::Serialize;

#[derive(Serialize)]
struct OkResp  { status: &'static str, result: &'static str, depth: usize, lang: &'static str, paradigm: &'static str }
#[derive(Serialize)]
struct ErrResp { status: &'static str, message: String,      depth: usize, lang: &'static str, paradigm: &'static str }

#[derive(Debug)]
struct BizError(String);
impl std::fmt::Display for BizError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result { write!(f, "{}", self.0) }
}

fn call_level(n: usize, fail: bool) -> Result<&'static str, BizError> {
    if n == 0 {
        if fail { return Err(BizError("error at leaf".into())) }
        return Ok("success");
    }
    call_level(n - 1, fail)
}

#[derive(serde::Deserialize)]
struct Query { #[serde(default)] error_rate: u8 }

fn should_fail(r: u8) -> bool {
    match r { 0 => false, 100 => true, r => rand::thread_rng().gen_range(0..100) < r }
}

#[get("/bench/health")]
async fn health() -> HttpResponse {
    HttpResponse::Ok().json(serde_json::json!({"status":"up","lang":"rust","paradigm":"value"}))
}

#[get("/bench/{depth}")]
async fn bench(p: web::Path<usize>, q: web::Query<Query>) -> HttpResponse {
    let depth = p.into_inner();
    match call_level(depth, should_fail(q.error_rate)) {
        Ok(_)  => HttpResponse::Ok().json(OkResp {
            status:"ok", result:"success", depth, lang:"rust", paradigm:"value"
        }),
        Err(e) => HttpResponse::InternalServerError().json(ErrResp {
            status:"error", message:e.to_string(), depth, lang:"rust", paradigm:"value"
        }),
    }
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    let port = std::env::var("PORT").unwrap_or("8083".into());
    println!("[rust 1.86] :{port}");
    HttpServer::new(|| {
        App::new()
            .service(health)  // health registrado antes de bench
            .service(bench)
    })
    .workers(2)
    .bind(format!("0.0.0.0:{port}"))?
    .run()
    .await
}
