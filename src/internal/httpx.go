package internal

import (
	"encoding/json"
	"net/http"

	"HW5/internal/api"
)

func WriteJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}

// write an error response in JSON format
func WriteError(w http.ResponseWriter, code int, errCode, msg, details string) {
	// create a details pointer only if details is non-empty, if not it will be nil
	var dptr *string
	if details != "" {
		dptr = &details
	}
	e := api.Error{Error: errCode, Message: msg, Details: dptr}
	WriteJSON(w, code, e)
}
