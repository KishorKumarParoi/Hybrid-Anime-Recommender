package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestGoAuthSignInAndVerify(t *testing.T) {
	// 1. Sign In as default admin
	loginPayload := map[string]string{
		"username": "admin",
		"password": "admin123",
	}
	body, _ := json.Marshal(loginPayload)
	req := httptest.NewRequest(http.MethodPost, "/api/v1/auth/signin", bytes.NewReader(body))
	w := httptest.NewRecorder()

	handleSignIn(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("Expected 200, got %d: %s", w.Code, w.Body.String())
	}

	var authResp AuthResponse
	if err := json.NewDecoder(w.Body).Decode(&authResp); err != nil {
		t.Fatalf("Failed to decode auth response: %v", err)
	}

	if authResp.AccessToken == "" {
		t.Fatalf("Expected non-empty access token")
	}

	// 2. Verify Token
	verifyReq := httptest.NewRequest(http.MethodGet, "/api/v1/auth/verify", nil)
	verifyReq.Header.Set("Authorization", "Bearer "+authResp.AccessToken)
	wVerify := httptest.NewRecorder()

	handleVerify(wVerify, verifyReq)
	if wVerify.Code != http.StatusOK {
		t.Fatalf("Expected 200 on verify, got %d: %s", wVerify.Code, wVerify.Body.String())
	}

	var verifyResp VerifyResponse
	json.NewDecoder(wVerify.Body).Decode(&verifyResp)
	if verifyResp.User.Username != "admin" {
		t.Errorf("Expected username 'admin', got '%s'", verifyResp.User.Username)
	}
}

func TestGoAuthSignUp(t *testing.T) {
	signUpPayload := map[string]interface{}{
		"username": "kenshiro",
		"email":    "kenshiro@hokuto.jp",
		"password": "atatatata2026!",
		"roles":    []string{"anime_enthusiast"},
	}
	body, _ := json.Marshal(signUpPayload)
	req := httptest.NewRequest(http.MethodPost, "/api/v1/auth/signup", bytes.NewReader(body))
	w := httptest.NewRecorder()

	handleSignUp(w, req)
	if w.Code != http.StatusCreated {
		t.Fatalf("Expected 201 Created, got %d: %s", w.Code, w.Body.String())
	}
}

func TestGoAuthHealth(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	w := httptest.NewRecorder()
	handleHealth(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("Expected 200, got %d", w.Code)
	}
}
