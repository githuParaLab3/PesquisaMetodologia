import http from 'k6/http';
import { check } from 'k6';

const BASES = {
    java:   'http://localhost:8080',
    nodejs: 'http://localhost:8081',
    go:     'http://localhost:8082',
    rust:   'http://localhost:8083',
};

const LANG       = __ENV.LANG       || 'java';
const DEPTH      = __ENV.DEPTH      || '1';
const ERROR_RATE = __ENV.ERROR_RATE || '0';
const BATTERY    = __ENV.BATTERY    || '1';
const PHASE      = __ENV.PHASE      || 'test';
const VUS        = parseInt(__ENV.VUS || '50');

const URL = `${BASES[LANG]}/bench/${DEPTH}?error_rate=${ERROR_RATE}`;

// summaryTrendStats força o k6 a calcular e expor p(50) e p(99) em values
export const options = {
    vus:      VUS,
    duration: PHASE === 'warmup' ? '30s' : '60s',
    summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(99)'],
};

export default function () {
    const res = http.get(URL);
    check(res, { 'status 200 ou 500': (r) => r.status === 200 || r.status === 500 });
}

export function handleSummary(data) {
    if (PHASE === 'warmup') {
        return { stdout: `  🔥 Aquecimento: ${LANG} depth=${DEPTH} err=${ERROR_RATE}%\n` };
    }

    const d   = data.metrics.http_req_duration;
    const tag = `${LANG}_depth${DEPTH}_err${ERROR_RATE}_bat${BATTERY}`;

    const p50 = d?.values?.med       ?? null;
    const p99 = d?.values?.['p(99)'] ?? null;

    const out = {
        scenario:   `${LANG}_depth${DEPTH}_err${ERROR_RATE}`,
        battery:    parseInt(BATTERY),
        lang:       LANG,
        depth:      parseInt(DEPTH),
        error_rate: parseInt(ERROR_RATE),
        vus:        VUS,
        p50_ms:     p50,
        p99_ms:     p99,
        avg_ms:     d?.values?.avg       ?? null,
        p90_ms:     d?.values?.['p(90)'] ?? null,
        min_ms:     d?.values?.min       ?? null,
        max_ms:     d?.values?.max       ?? null,
        rps:        data.metrics.http_reqs?.values?.rate  ?? null,
        total_reqs: data.metrics.http_reqs?.values?.count ?? null,
    };

    const fmt = (v) => v != null ? v.toFixed(2) : 'null';
    return {
        [`results/${tag}.json`]: JSON.stringify(out, null, 2),
        stdout: `  ✅ ${tag} | P50: ${fmt(p50)}ms | P99: ${fmt(p99)}ms | RPS: ${out.rps?.toFixed(0)} | Reqs: ${out.total_reqs}\n`,
    };
}