package com.research.errorperf.exception;

/**
 * Exceção de negócio — ao ser lançada, força a JVM a executar stack walking
 * e alocar o objeto de exceção na heap, pressionando o G1GC.
 */
public class BusinessException extends RuntimeException {
    public BusinessException(String message) {
        super(message);
    }
}
