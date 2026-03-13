'use strict';
const express = require('express');
const app = express();

function callLevel(remaining, shouldFail) {
    if (remaining <= 0) {
        if (shouldFail) throw new Error('error at leaf');
        return 'success';
    }
    return callLevel(remaining - 1, shouldFail);
}

function shouldFail(rate) {
    if (rate === 0)   return false;
    if (rate === 100) return true;
    return Math.random() * 100 < rate;
}

// HEALTH DEVE VIR ANTES DE /:depth
app.get('/bench/health', (_, res) => {
    res.json({ status: 'up', lang: 'nodejs', paradigm: 'exception' });
});

app.get('/bench/:depth', async (req, res) => {
    const depth = parseInt(req.params.depth);
    const rate  = parseInt(req.query.error_rate ?? '0');
    try {
        const result = callLevel(depth, shouldFail(rate));
        res.json({ status: 'ok', result, depth, lang: 'nodejs', paradigm: 'exception' });
    } catch (e) {
        res.status(500).json({ status: 'error', message: e.message, depth, lang: 'nodejs', paradigm: 'exception' });
    }
});

app.listen(8081, () => console.log('[nodejs 22 LTS] :8081'));
