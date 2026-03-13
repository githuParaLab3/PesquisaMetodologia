package com.research.errorperf.controller;

import com.research.errorperf.exception.BusinessException;
import com.research.errorperf.exception.ExceptionService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

/**
 * Java 21 LTS — Paradigma nativo: Exceções (throw / catch)
 *
 * Rota: GET /bench/{depth}?error_rate={0|5|50|100}
 *   depth      → profundidade da pilha (1, 25, 50)
 *   error_rate → percentual de requisições que disparam exceção
 */
@RestController
@RequestMapping("/bench")
public class BenchmarkController {

    private final ExceptionService exceptionService;

    public BenchmarkController(ExceptionService e) {
        this.exceptionService = e;
    }

    @GetMapping("/{depth}")
    public ResponseEntity<Map<String, Object>> bench(
            @PathVariable int depth,
            @RequestParam(defaultValue = "0") int error_rate) {
        try {
            String result = exceptionService.process(depth, shouldFail(error_rate));
            return ResponseEntity.ok(Map.of(
                "status",   "ok",
                "result",   result,
                "depth",    depth,
                "lang",     "java",
                "paradigm", "exception"
            ));
        } catch (BusinessException ex) {
            return ResponseEntity.status(500).body(Map.of(
                "status",   "error",
                "message",  ex.getMessage(),
                "depth",    depth,
                "lang",     "java",
                "paradigm", "exception"
            ));
        }
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        return ResponseEntity.ok(Map.of(
            "status",   "up",
            "lang",     "java",
            "paradigm", "exception"
        ));
    }

    private boolean shouldFail(int rate) {
        if (rate == 0)   return false;
        if (rate == 100) return true;
        return (System.nanoTime() % 100) < rate;
    }
}
