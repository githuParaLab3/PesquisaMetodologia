package com.research.errorperf.exception;
import org.springframework.stereotype.Service;

/**
 * Simula pilha de chamadas recursiva com profundidade configurável.
 * No nó folha (depth=0), lança BusinessException se shouldFail=true.
 * A JVM percorre toda a pilha retroativamente (stack unwinding)
 * e constrói o stack trace — custo proporcional à profundidade N.
 */
@Service
public class ExceptionService {

    public String process(int depth, boolean shouldFail) {
        return callLevel(depth, shouldFail);
    }

    private String callLevel(int remaining, boolean shouldFail) {
        if (remaining <= 0) {
            if (shouldFail) throw new BusinessException("error at leaf");
            return "success";
        }
        return callLevel(remaining - 1, shouldFail);
    }
}
