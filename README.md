# PesquisaMetodologia
## O Custo Computacional da Falha — IFBA / Ciência da Computação


---

## Linguagens e versões (seção 5.2)

| Linguagem | Versão   | Runtime / GC                         | Paradigma nativo  | Porta |
|-----------|----------|--------------------------------------|-------------------|-------|
| Java      | 21 LTS   | JVM HotSpot, G1GC                    | Exceções          | 8080  |
| Node.js   | 22 LTS   | V8, async/await, event loop          | Exceções          | 8081  |
| Go        | 1.24     | Goroutines, GC concorrente           | Valores de retorno| 8082  |
| Rust      | 1.86     | Compilação nativa, sem GC, ownership | Valores de retorno| 8083  |

---

## Matriz de cenários — 48 total (seção 5.4)

12 cenários por linguagem = 3 profundidades × 4 taxas de erro

| Profundidade | Erro 0%   | Erro 5%      | Erro 50%      | Erro 100%   |
|:------------:|:---------:|:------------:|:-------------:|:-----------:|
| N=1  (Rasa)  | Controle  | Falha comum  | Instabilidade | Estresse    |
| N=25 (Média) | Controle  | Falha comum  | Instabilidade | Estresse    |
| N=50 (Profunda)| Controle| Falha comum  | Instabilidade | Estresse    |

× 4 linguagens = **48 cenários** × 3 baterias = **144 execuções de 60s**

---

## Como executar (PowerShell dentro da pasta PesquisaMetodologia/)

```powershell
# 1. Build (primeira vez ~20 min)
docker-compose build

# 2. Subir containers
docker-compose up -d

# 3. Verificar saúde
curl http://localhost:8080/bench/health
curl http://localhost:8081/bench/health
curl http://localhost:8082/bench/health
curl http://localhost:8083/bench/health

# 4. Rodar testes (~3h)
python run_tests.py

# 5. Gerar gráficos
python analysis/analyze.py

# 6. Parar containers
docker-compose down
```

---

## Saídas geradas em analysis/output/

| Arquivo | Objetivo do pré-projeto |
|---|---|
| `fig1_degradacao_p50_vs_taxa_erro.png` | a) Perfil linear vs não-linear |
| `fig2_p99_vs_profundidade.png` | b) Correlação profundidade × latência de cauda |
| `fig3_comparacao_exception_vs_value_N50.png` | c/d) Comparação direta + ponto de inflexão |
| `fig4_heatmap_delta_degradacao.png` | Seção 5.6 — delta de degradação |
| `fig5_cpu_ram.png` | Consumo de infraestrutura (CPU e RAM) |
| `resultados_completos.csv` | Tabela completa para análise estatística |
