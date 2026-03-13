package main

import (
	"encoding/json"
	"log"
	"math/rand"
	"net/http"
	"os"
	"strconv"
)

type BizError struct{ Message string }
func (e *BizError) Error() string { return e.Message }

func callLevel(n int, fail bool) (string, error) {
	if n <= 0 {
		if fail { return "", &BizError{"error at leaf"} }
		return "success", nil
	}
	return callLevel(n-1, fail)
}

func shouldFail(rate int) bool {
	if rate == 0   { return false }
	if rate == 100 { return true }
	return rand.Intn(100) < rate
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}

func main() {
	mux := http.NewServeMux()

	// /bench/health — deve ser registrado ANTES de /bench/{depth}
	mux.HandleFunc("/bench/health", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, map[string]string{"status": "up", "lang": "go", "paradigm": "value"})
	})

	mux.HandleFunc("/bench/", func(w http.ResponseWriter, r *http.Request) {
		// extrai depth do path: /bench/1 → "1"
		part := r.URL.Path[len("/bench/"):]
		depth, err := strconv.Atoi(part)
		if err != nil {
			http.Error(w, "invalid depth", 400)
			return
		}
		rate, _ := strconv.Atoi(r.URL.Query().Get("error_rate"))
		result, bErr := callLevel(depth, shouldFail(rate))
		if bErr != nil {
			writeJSON(w, 500, map[string]any{
				"status": "error", "message": bErr.Error(),
				"depth": depth, "lang": "go", "paradigm": "value",
			})
			return
		}
		writeJSON(w, 200, map[string]any{
			"status": "ok", "result": result,
			"depth": depth, "lang": "go", "paradigm": "value",
		})
	})

	port := os.Getenv("PORT")
	if port == "" { port = "8082" }
	log.Printf("[go 1.24] :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, mux))
}
