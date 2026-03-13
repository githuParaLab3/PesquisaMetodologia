"""
run_tests.py — 48 cenários × 3 baterias conforme metodologia (seção 5.4 e 5.5)

Matriz de cenários:
  Java   (exceções)        → 12 cenários: 3 depths × 4 error_rates
  Node.js (exceções)       → 12 cenários: 3 depths × 4 error_rates
  Go     (valores retorno) → 12 cenários: 3 depths × 4 error_rates
  Rust   (valores retorno) → 12 cenários: 3 depths × 4 error_rates
  Total: 48 cenários × 3 baterias = 144 execuções de 60s + aquecimento 30s

Uso: python run_tests.py
"""

import subprocess
import sys
import time
import json
import threading
from pathlib import Path
from datetime import datetime
import urllib.request

# ── Configuração conforme metodologia ─────────────────────────────────────────

# Cada linguagem mapeada ao seu paradigma nativo (seção 5.2 do pré-projeto)
LANG_PARADIGM = {
    "java":   "exception",
    "nodejs": "exception",
    "go":     "value",
    "rust":   "value",
}

DEPTHS      = [1, 25, 50]
ERROR_RATES = [0, 5, 50, 100]
BATTERIES   = 3
VUS         = 50

PORTS = {
    "java":   8080,
    "nodejs": 8081,
    "go":     8082,
    "rust":   8083,
}

CONTAINER_NAMES = {
    "java":   "bench-java",
    "nodejs": "bench-nodejs",
    "go":     "bench-go",
    "rust":   "bench-rust",
}

results_dir = Path("results")
results_dir.mkdir(exist_ok=True)

# ── Verificar serviços ────────────────────────────────────────────────────────

def check_services():
    print("Verificando serviços...", end=" ", flush=True)
    for lang, port in PORTS.items():
        try:
            urllib.request.urlopen(f"http://localhost:{port}/bench/health", timeout=3)
        except Exception:
            print(f"\n❌ {lang} (:{port}) não está respondendo.")
            print("   Execute: docker-compose up -d")
            sys.exit(1)
    print("✅ todos prontos!\n")

# ── Coletar CPU e RAM via docker stats ────────────────────────────────────────

class StatsCollector:
    def __init__(self, container: str):
        self.container = container
        self.samples   = []
        self._stop     = threading.Event()
        self._thread   = None

    def start(self):
        self._stop.clear()
        self.samples = []
        self._thread = threading.Thread(target=self._collect, daemon=True)
        self._thread.start()

    def stop(self) -> dict:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        if not self.samples:
            return {"cpu_avg_pct": None, "cpu_max_pct": None,
                    "ram_avg_mb": None, "ram_max_mb": None}
        cpus = [s["cpu"] for s in self.samples if s["cpu"] is not None]
        rams = [s["ram"] for s in self.samples if s["ram"] is not None]
        return {
            "cpu_avg_pct": round(sum(cpus)/len(cpus), 2) if cpus else None,
            "cpu_max_pct": round(max(cpus), 2)           if cpus else None,
            "ram_avg_mb":  round(sum(rams)/len(rams), 2) if rams else None,
            "ram_max_mb":  round(max(rams), 2)           if rams else None,
        }

    def _collect(self):
        while not self._stop.is_set():
            try:
                out = subprocess.run(
                    ["docker", "stats", self.container, "--no-stream",
                     "--format", "{{.CPUPerc}},{{.MemUsage}}"],
                    capture_output=True, text=True, timeout=3
                ).stdout.strip()
                if out:
                    parts   = out.split(",")
                    cpu_str = parts[0].replace("%", "").strip()
                    mem_str = parts[1].split("/")[0].strip() if len(parts) > 1 else ""
                    cpu = float(cpu_str) if cpu_str else None
                    ram = self._parse_mem(mem_str)
                    self.samples.append({"cpu": cpu, "ram": ram})
            except Exception:
                pass
            time.sleep(1)

    @staticmethod
    def _parse_mem(s: str):
        try:
            s = s.strip()
            if "GiB" in s: return float(s.replace("GiB","")) * 1024
            if "MiB" in s: return float(s.replace("MiB",""))
            if "kB"  in s: return float(s.replace("kB","")) / 1024
        except Exception:
            pass
        return None

# ── Rodar k6 ─────────────────────────────────────────────────────────────────

def run_k6(lang, depth, rate, battery, phase="test"):
    cmd = [
        "k6", "run",
        "--env", f"LANG={lang}",
        "--env", f"DEPTH={depth}",
        "--env", f"ERROR_RATE={rate}",
        "--env", f"BATTERY={battery}",
        "--env", f"PHASE={phase}",
        "--env", f"VUS={VUS}",
        "--quiet",
        "k6/bench.js",
    ]
    return subprocess.run(cmd, capture_output=True, text=True)

# ── Loop principal ────────────────────────────────────────────────────────────

def main():
    check_services()

    # 48 cenários: cada linguagem com seu paradigma nativo
    scenarios = [
        (lang, depth, rate)
        for lang  in LANG_PARADIGM
        for depth in DEPTHS
        for rate  in ERROR_RATES
    ]

    total   = len(scenarios) * BATTERIES
    current = 0
    errors  = []
    start   = datetime.now()

    est_min = (total * 65 + len(scenarios) * 35) // 60

    print("=" * 65)
    print(f"  Benchmark — {len(scenarios)} cenários × {BATTERIES} baterias = {total} execuções")
    print(f"  VUs: {VUS} | Aquecimento: 30s | Duração por bateria: 60s")
    print(f"  Tempo estimado: ~{est_min} minutos (~{est_min//60}h{est_min%60:02d}min)")
    print(f"  Início: {start.strftime('%H:%M:%S')}")
    print()
    print(f"  Paradigmas:")
    for lang, paradigm in LANG_PARADIGM.items():
        print(f"    {lang:8} → {paradigm}")
    print("=" * 65)

    for lang, depth, rate in scenarios:
        paradigm    = LANG_PARADIGM[lang]
        scenario_tag = f"{lang}_depth{depth}_err{rate}"
        container   = CONTAINER_NAMES[lang]

        print(f"\n{'─'*65}")
        print(f"  Cenário: {scenario_tag}  [{paradigm}]")

        # Aquecimento 30s (conforme seção 5.5)
        print(f"  🔥 Aquecendo 30s...", end=" ", flush=True)
        run_k6(lang, depth, rate, battery=0, phase="warmup")
        print("pronto")

        for battery in range(1, BATTERIES + 1):
            current += 1
            tag   = f"{scenario_tag}_bat{battery}"
            label = f"  [{current:3d}/{total}] bateria {battery}/{BATTERIES}"

            print(f"{label}", end=" ", flush=True)
            t0 = time.time()

            collector = StatsCollector(container)
            collector.start()
            result = run_k6(lang, depth, rate, battery, phase="test")
            stats  = collector.stop()
            elapsed = time.time() - t0

            if result.returncode != 0:
                print(f"❌ ERRO ({elapsed:.0f}s)")
                errors.append(tag)
                (results_dir / f"{tag}_ERROR.log").write_text(
                    result.stderr + "\n" + result.stdout
                )
            else:
                # Enriquecer JSON com CPU/RAM e paradigma
                result_file = results_dir / f"{tag}.json"
                if result_file.exists():
                    data = json.loads(result_file.read_text())
                    data["paradigm"] = paradigm
                    data.update(stats)
                    result_file.write_text(json.dumps(data, indent=2))

                p50 = rps = "?"
                for line in result.stdout.splitlines():
                    if "P50:" in line:
                        for part in line.strip().split("|"):
                            if "P50:" in part: p50 = part.split(":")[1].strip()
                            if "RPS:" in part: rps = part.split(":")[1].strip()

                cpu_info = f" CPU:{stats['cpu_avg_pct']}%" if stats['cpu_avg_pct'] else ""
                ram_info = f" RAM:{stats['ram_avg_mb']}MB" if stats['ram_avg_mb'] else ""
                print(f"✅ P50={p50} RPS={rps}{cpu_info}{ram_info} ({elapsed:.0f}s)")

            if battery < BATTERIES:
                time.sleep(3)

        time.sleep(3)

    elapsed_min = int((datetime.now() - start).seconds / 60)
    n_results   = len(list(results_dir.glob("*_bat*.json")))

    print("\n" + "=" * 65)
    print(f"  ✅ Concluído em {elapsed_min} minutos")
    print(f"  📁 {n_results} arquivos em: results/")

    if errors:
        print(f"\n  ⚠️  {len(errors)} execuções com erro:")
        for e in errors:
            print(f"     - {e}")

    print(f"\n  Próximo passo: python analysis/analyze.py")
    print("=" * 65)

if __name__ == "__main__":
    main()
