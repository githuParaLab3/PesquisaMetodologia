"""
analyze.py — Agrega resultados e gera gráficos conforme objetivos do pré-projeto:
  a) Perfil de degradação linear vs não-linear (P50 vs taxa de erro)
  b) Correlação profundidade × latência de cauda (P99 vs depth)
  c) Comparação direta exception vs value (barras por linguagem)
  d) Ponto de inflexão entre os paradigmas
  + Heatmap delta de degradação (seção 5.6)
  + CPU e RAM por linguagem

Uso: python analysis/analyze.py
"""

import json
import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ── Configuração ──────────────────────────────────────────────────────────────

EXCECAO  = ["java", "nodejs"]
VALOR    = ["go", "rust"]
LANGS    = EXCECAO + VALOR
DEPTHS   = [1, 25, 50]
ERR_RATES = [0, 5, 50, 100]

COLORS = {
    "java":   "#5382a1",
    "nodejs": "#83CD29",
    "go":     "#00ACD7",
    "rust":   "#CE422B",
}

PARADIGM_LABEL = {
    "java":   "Exceção",
    "nodejs": "Exceção",
    "go":     "Valor de Retorno",
    "rust":   "Valor de Retorno",
}

sns.set_theme(style="whitegrid", font_scale=1.1)
plt.rcParams["figure.dpi"] = 150

output_dir = Path("analysis/output")
output_dir.mkdir(parents=True, exist_ok=True)

# ── Carregar resultados ───────────────────────────────────────────────────────

results_dir = Path("results")
files = [f for f in sorted(results_dir.glob("*.json")) if "ERROR" not in f.name]

if not files:
    print("❌ Nenhum resultado em results/. Execute: python run_tests.py")
    sys.exit(1)

rows = []
for f in files:
    try:
        rows.append(json.loads(f.read_text()))
    except Exception as e:
        print(f"⚠️  {f.name}: {e}")

raw = pd.DataFrame(rows)
print(f"✅ {len(raw)} execuções carregadas — {raw['scenario'].nunique()} cenários únicos\n")

# Agregar 3 baterias
df = (
    raw.groupby(["lang", "depth", "error_rate"])
    .agg(
        p50_ms        = ("p50_ms",  "mean"),
        p99_ms        = ("p99_ms",  "mean"),
        avg_ms        = ("avg_ms",  "mean"),
        rps           = ("rps",     "mean"),
        stddev_bat    = ("p50_ms",  "std"),
        total_reqs    = ("total_reqs", "sum"),
    )
    .reset_index()
)

# Adiciona CPU/RAM se disponíveis
if "cpu_avg_pct" in raw.columns:
    cpu_ram = (
        raw.groupby(["lang", "depth", "error_rate"])
        .agg(cpu_avg_pct=("cpu_avg_pct","mean"), ram_avg_mb=("ram_avg_mb","mean"))
        .reset_index()
    )
    df = df.merge(cpu_ram, on=["lang","depth","error_rate"], how="left")

# Delta de degradação vs baseline 0% erro (seção 5.6)
baseline = df[df["error_rate"] == 0][["lang","depth","p50_ms"]].rename(columns={"p50_ms":"p50_base"})
df = df.merge(baseline, on=["lang","depth"], how="left")
df["delta_pct"] = ((df["p50_ms"] - df["p50_base"]) / df["p50_base"]) * 100

print(f"📊 Gerando gráficos em {output_dir}/\n")

# ── Figura 1: Degradação P50 vs Taxa de Erro — objetivo a) ───────────────────
# "Caracterizar o perfil de degradação (linear ou exponencial)"

fig, axes = plt.subplots(1, 3, figsize=(18, 5), sharey=False)
fig.suptitle(
    "Obj. a) Perfil de Degradação — P50 vs Taxa de Erro por Profundidade de Pilha",
    fontsize=12, fontweight="bold"
)
for ax, depth in zip(axes, DEPTHS):
    sub = df[df["depth"] == depth]
    for lang in LANGS:
        d = sub[sub["lang"] == lang].sort_values("error_rate")
        if d.empty: continue
        ls = "--" if lang in EXCECAO else "-"
        mk = "X"  if lang in EXCECAO else "o"
        ax.plot(d["error_rate"], d["p50_ms"],
                color=COLORS[lang], linestyle=ls, marker=mk,
                linewidth=2, label=f"{lang} ({PARADIGM_LABEL[lang][:3]})")
    ax.set_title(f"Profundidade N={depth}")
    ax.set_xlabel("Taxa de Erro (%)")
    ax.set_ylabel("P50 Latência (ms)")
    ax.set_xticks(ERR_RATES)
    ax.set_xticklabels([f"{r}%" for r in ERR_RATES])

handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.08))
plt.tight_layout()
p = output_dir / "fig1_degradacao_p50_vs_taxa_erro.png"
plt.savefig(p, bbox_inches="tight"); plt.close()
print(f"  ✅ {p.name}")

# ── Figura 2: P99 vs Profundidade — objetivo b) ───────────────────────────────
# "Demonstrar correlação entre profundidade da pilha e latência de cauda"

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle(
    "Obj. b) Latência de Cauda P99 vs Profundidade — 100% Erros (Stack Walking)",
    fontsize=12, fontweight="bold"
)
for ax, (grupo, langs) in enumerate(zip(["Exceções", "Valores de Retorno"], [EXCECAO, VALOR])):
    a = axes[ax]
    sub = df[(df["error_rate"] == 100) & (df["lang"].isin(langs))]
    for lang in langs:
        d = sub[sub["lang"] == lang].sort_values("depth")
        if d.empty: continue
        a.plot(d["depth"], d["p99_ms"],
               color=COLORS[lang], marker="o", linewidth=2.5, label=lang)
        a.fill_between(d["depth"],
                       d["p99_ms"] - d["stddev_bat"].fillna(0),
                       d["p99_ms"] + d["stddev_bat"].fillna(0),
                       color=COLORS[lang], alpha=0.12)
    a.set_title(grupo)
    a.set_xlabel("Profundidade N")
    a.set_ylabel("P99 Latência (ms)")
    a.set_xticks(DEPTHS)
    a.legend()

plt.tight_layout()
p = output_dir / "fig2_p99_vs_profundidade.png"
plt.savefig(p, bbox_inches="tight"); plt.close()
print(f"  ✅ {p.name}")

# ── Figura 3: Comparação direta exception vs value — objetivo c/d) ────────────
# Barras agrupadas por paradigma em N=50, todos os error_rates

fig, axes = plt.subplots(1, 4, figsize=(20, 5))
fig.suptitle(
    "Obj. c/d) Exceções vs Valores de Retorno — N=50 | P50 Latência",
    fontsize=12, fontweight="bold"
)
deep = df[df["depth"] == 50].sort_values("error_rate")
x    = list(range(len(ERR_RATES)))
w    = 0.2
for i, lang in enumerate(LANGS):
    ax = axes[i // 2 * 0 + i % 4]  # 4 subplots, um por lang
    d = deep[deep["lang"] == lang]
    if d.empty: continue
    axes[i].bar(x, d["p50_ms"], width=0.6, color=COLORS[lang], alpha=0.85, label=lang)
    axes[i].set_title(f"{lang.upper()}\n({PARADIGM_LABEL[lang]})")
    axes[i].set_xlabel("Taxa de Erro")
    axes[i].set_xticks(x)
    axes[i].set_xticklabels(["0%","5%","50%","100%"])
    axes[i].set_ylabel("P50 (ms)")

plt.tight_layout()
p = output_dir / "fig3_comparacao_exception_vs_value_N50.png"
plt.savefig(p, bbox_inches="tight"); plt.close()
print(f"  ✅ {p.name}")

# ── Figura 4: Heatmap delta de degradação — seção 5.6 ─────────────────────────

fig, axes = plt.subplots(1, 4, figsize=(22, 5))
fig.suptitle(
    "Delta de Degradação % vs Baseline (0% erro) — P50 | Seção 5.6",
    fontsize=12, fontweight="bold"
)
for ax, lang in zip(axes, LANGS):
    sub   = df[df["lang"] == lang]
    pivot = sub.pivot(index="depth", columns="error_rate", values="delta_pct")
    pivot = pivot.reindex(index=DEPTHS, columns=ERR_RATES)
    sns.heatmap(pivot, ax=ax, cmap="RdYlGn_r",
                annot=True, fmt=".0f", linewidths=0.5,
                vmin=0, vmax=500, cbar=(lang == LANGS[-1]))
    ax.set_title(f"{lang.upper()}\n({PARADIGM_LABEL[lang]})")
    ax.set_xlabel("Taxa de Erro (%)")
    ax.set_ylabel("Profundidade N")

plt.tight_layout()
p = output_dir / "fig4_heatmap_delta_degradacao.png"
plt.savefig(p, bbox_inches="tight"); plt.close()
print(f"  ✅ {p.name}")

# ── Figura 5: CPU e RAM (se disponível) ───────────────────────────────────────
if "cpu_avg_pct" in df.columns and df["cpu_avg_pct"].notna().any():
    sub = df[(df["depth"] == 50) & (df["error_rate"] == 100)]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Consumo de Infraestrutura — N=50 | 100% erro", fontsize=12, fontweight="bold")
    for ax, metric, label in zip(axes, ["cpu_avg_pct","ram_avg_mb"], ["CPU Médio (%)","RAM Média (MB)"]):
        colors = [COLORS[l] for l in sub["lang"]]
        ax.bar(sub["lang"], sub[metric], color=colors, alpha=0.85)
        ax.set_title(label)
        ax.set_ylabel(label)
        ax.set_xlabel("Linguagem")
    plt.tight_layout()
    p = output_dir / "fig5_cpu_ram.png"
    plt.savefig(p, bbox_inches="tight"); plt.close()
    print(f"  ✅ {p.name}")

# ── CSV completo ──────────────────────────────────────────────────────────────
csv_path = output_dir / "resultados_completos.csv"
df.to_csv(csv_path, index=False, float_format="%.3f")
print(f"  ✅ {csv_path.name}")

# ── Resumo terminal ───────────────────────────────────────────────────────────
print()
print("=" * 70)
print("  RESUMO — P50 (ms) | Profundidade N=50 | 100% erro")
print("=" * 70)
tab = df[(df["depth"]==50)&(df["error_rate"]==100)][["lang","p50_ms","p99_ms","rps","delta_pct"]]
tab = tab.copy()
tab["paradigma"] = tab["lang"].map(PARADIGM_LABEL)
tab = tab[["lang","paradigma","p50_ms","p99_ms","rps","delta_pct"]].sort_values("lang")
tab.columns = ["Lang","Paradigma","P50 (ms)","P99 (ms)","RPS","Delta %"]
print(tab.to_string(index=False, float_format="%.2f"))

# ── Objetivo d) Ponto de inflexão ─────────────────────────────────────────────
print()
print("  Obj. d) PONTO DE INFLEXÃO — Exceções vs Valores de Retorno")
print("-" * 70)
for depth in DEPTHS:
    sub = df[df["depth"] == depth]
    exc_vals = sub[sub["lang"].isin(EXCECAO)].groupby("error_rate")["p50_ms"].mean()
    val_vals = sub[sub["lang"].isin(VALOR)].groupby("error_rate")["p50_ms"].mean()
    for rate in ERR_RATES:
        if rate in exc_vals.index and rate in val_vals.index:
            e, v = exc_vals[rate], val_vals[rate]
            if e > v:
                print(f"  N={depth:2d}  →  inflexão em {rate:3d}% erro  "
                      f"(exc={e:.2f}ms  val={v:.2f}ms  {e/v:.1f}x)")
                break

print()
print(f"  📁 Gráficos: {output_dir.absolute()}")
print("=" * 70)
