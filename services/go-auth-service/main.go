package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"
)

// User represents persistent user identity in PostgreSQL/MongoDB
type User struct {
	ID           string    `json:"id"`
	Username     string    `json:"username"`
	Email        string    `json:"email"`
	PasswordHash string    `json:"-"`
	Roles        []string  `json:"roles"`
	CreatedAt    time.Time `json:"created_at"`
}

type SignUpRequest struct {
	Username string   `json:"username"`
	Email    string   `json:"email"`
	Password string   `json:"password"`
	Roles    []string `json:"roles"`
}

type SignInRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

type AuthResponse struct {
	Status      string   `json:"status"`
	AccessToken string   `json:"access_token"`
	TokenType   string   `json:"token_type"`
	ExpiresIn   int64    `json:"expires_in"`
	User        UserInfo `json:"user"`
}

type UserInfo struct {
	ID       string   `json:"id"`
	Username string   `json:"username"`
	Email    string   `json:"email"`
	Roles    []string `json:"roles"`
}

type VerifyResponse struct {
	Status string   `json:"status"`
	Valid  bool     `json:"valid"`
	User   UserInfo `json:"user"`
}

type HealthResponse struct {
	Status    string `json:"status"`
	Service   string `json:"service"`
	UptimeSec int64  `json:"uptime_sec"`
	Users     int    `json:"active_users_cached"`
}

var (
	jwtSecret   = []byte(getEnv("JWT_SECRET_KEY", "har-super-secret-jwt-key-2026-production-ready"))
	startTime   = time.Now()
	usersDBLock sync.RWMutex
	usersDB     = make(map[string]*User)
)

func init() {
	// Pre-seed default enterprise users (admin, researcher, user)
	seedUser("admin", "admin@anime.ai", "admin123", []string{"admin", "researcher", "viewer"})
	seedUser("researcher", "researcher@anime.ai", "research123", []string{"researcher", "viewer"})
	seedUser("user", "user@anime.ai", "user123", []string{"viewer"})
}

func seedUser(username, email, password string, roles []string) {
	u := &User{
		ID:           fmt.Sprintf("usr_%x", sha256.Sum256([]byte(username)))[:14],
		Username:     username,
		Email:        email,
		PasswordHash: hashPassword(password),
		Roles:        roles,
		CreatedAt:    time.Now().UTC(),
	}
	usersDB[strings.ToLower(username)] = u
}

func hashPassword(password string) string {
	h := sha256.New()
	h.Write([]byte(password + ":salt-anime-2026"))
	return fmt.Sprintf("%x", h.Sum(nil))
}

func checkPassword(password, hash string) bool {
	return hashPassword(password) == hash
}

// Minimal, zero-dependency JWT HS256 Token Creation
func generateJWT(user *User) (string, error) {
	headerJSON := `{"alg":"HS256","typ":"JWT"}`
	headerB64 := base64.RawURLEncoding.EncodeToString([]byte(headerJSON))

	now := time.Now().UTC()
	exp := now.Add(24 * time.Hour).Unix()

	claims := map[string]interface{}{
		"sub":   user.Username,
		"uid":   user.ID,
		"email": user.Email,
		"roles": user.Roles,
		"iat":   now.Unix(),
		"exp":   exp,
	}

	claimsBytes, err := json.Marshal(claims)
	if err != nil {
		return "", err
	}
	payloadB64 := base64.RawURLEncoding.EncodeToString(claimsBytes)

	signingInput := headerB64 + "." + payloadB64
	mac := hmac.New(sha256.New, jwtSecret)
	mac.Write([]byte(signingInput))
	signatureB64 := base64.RawURLEncoding.EncodeToString(mac.Sum(nil))

	return signingInput + "." + signatureB64, nil
}

// JWT Token Verification
func verifyJWT(tokenStr string) (map[string]interface{}, error) {
	parts := strings.Split(tokenStr, ".")
	if len(parts) != 3 {
		return nil, fmt.Errorf("malformed token")
	}

	signingInput := parts[0] + "." + parts[1]
	mac := hmac.New(sha256.New, jwtSecret)
	mac.Write([]byte(signingInput))
	expectedSig := mac.Sum(nil)

	actualSig, err := base64.RawURLEncoding.DecodeString(parts[2])
	if err != nil || !hmac.Equal(actualSig, expectedSig) {
		return nil, fmt.Errorf("invalid token signature")
	}

	payloadBytes, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return nil, fmt.Errorf("invalid payload encoding")
	}

	var claims map[string]interface{}
	if err := json.Unmarshal(payloadBytes, &claims); err != nil {
		return nil, fmt.Errorf("invalid claims JSON")
	}

	if expFloat, ok := claims["exp"].(float64); ok {
		if int64(expFloat) < time.Now().UTC().Unix() {
			return nil, fmt.Errorf("token expired")
		}
	}

	return claims, nil
}

func enableCORS(w http.ResponseWriter) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
}

// ─── Handlers ────────────────────────────────────────────────────────────────

func handleSignUp(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}
	if r.Method != http.MethodPost {
		http.Error(w, `{"error":"Method not allowed"}`, http.StatusMethodNotAllowed)
		return
	}

	var req SignUpRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"Invalid request payload"}`, http.StatusBadRequest)
		return
	}

	req.Username = strings.TrimSpace(req.Username)
	req.Email = strings.TrimSpace(req.Email)
	if req.Username == "" || req.Password == "" {
		http.Error(w, `{"error":"Username and password are required"}`, http.StatusBadRequest)
		return
	}

	usersDBLock.Lock()
	defer usersDBLock.Unlock()

	key := strings.ToLower(req.Username)
	if _, exists := usersDB[key]; exists {
		http.Error(w, `{"error":"User already exists with this username"}`, http.StatusConflict)
		return
	}

	roles := req.Roles
	if len(roles) == 0 {
		roles = []string{"viewer"}
	}

	newUser := &User{
		ID:           fmt.Sprintf("usr_%x", sha256.Sum256([]byte(req.Username+time.Now().String())))[:14],
		Username:     req.Username,
		Email:        req.Email,
		PasswordHash: hashPassword(req.Password),
		Roles:        roles,
		CreatedAt:    time.Now().UTC(),
	}
	usersDB[key] = newUser

	token, err := generateJWT(newUser)
	if err != nil {
		http.Error(w, `{"error":"Failed to generate auth token"}`, http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(AuthResponse{
		Status:      "success",
		AccessToken: token,
		TokenType:   "Bearer",
		ExpiresIn:   86400,
		User: UserInfo{
			ID:       newUser.ID,
			Username: newUser.Username,
			Email:    newUser.Email,
			Roles:    newUser.Roles,
		},
	})
}

func handleSignIn(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}
	if r.Method != http.MethodPost {
		http.Error(w, `{"error":"Method not allowed"}`, http.StatusMethodNotAllowed)
		return
	}

	var req SignInRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"Invalid request payload"}`, http.StatusBadRequest)
		return
	}

	usersDBLock.RLock()
	user, exists := usersDB[strings.ToLower(strings.TrimSpace(req.Username))]
	usersDBLock.RUnlock()

	if !exists || !checkPassword(req.Password, user.PasswordHash) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusUnauthorized)
		w.Write([]byte(`{"error":"Invalid username or password"}`))
		return
	}

	token, err := generateJWT(user)
	if err != nil {
		http.Error(w, `{"error":"Failed to generate auth token"}`, http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(AuthResponse{
		Status:      "success",
		AccessToken: token,
		TokenType:   "Bearer",
		ExpiresIn:   86400,
		User: UserInfo{
			ID:       user.ID,
			Username: user.Username,
			Email:    user.Email,
			Roles:    user.Roles,
		},
	})
}

func handleVerify(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
		return
	}

	authHeader := r.Header.Get("Authorization")
	if !strings.HasPrefix(authHeader, "Bearer ") {
		http.Error(w, `{"error":"Missing or invalid Authorization header"}`, http.StatusUnauthorized)
		return
	}

	tokenStr := strings.TrimPrefix(authHeader, "Bearer ")
	claims, err := verifyJWT(tokenStr)
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"%s"}`, err.Error()), http.StatusUnauthorized)
		return
	}

	username, _ := claims["sub"].(string)
	uid, _ := claims["uid"].(string)
	email, _ := claims["email"].(string)

	var roles []string
	if rawRoles, ok := claims["roles"].([]interface{}); ok {
		for _, rr := range rawRoles {
			if s, ok := rr.(string); ok {
				roles = append(roles, s)
			}
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(VerifyResponse{
		Status: "valid",
		Valid:  true,
		User: UserInfo{
			ID:       uid,
			Username: username,
			Email:    email,
			Roles:    roles,
		},
	})
}

func handleHealth(w http.ResponseWriter, r *http.Request) {
	enableCORS(w)
	usersDBLock.RLock()
	userCount := len(usersDB)
	usersDBLock.RUnlock()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(HealthResponse{
		Status:    "healthy",
		Service:   "go-auth-service",
		UptimeSec: int64(time.Since(startTime).Seconds()),
		Users:     userCount,
	})
}

func getEnv(key, defaultVal string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return defaultVal
}

func main() {
	port := getEnv("PORT", "8081")
	mux := http.NewServeMux()

	mux.HandleFunc("/api/v1/auth/signup", handleSignUp)
	mux.HandleFunc("/api/v1/auth/signin", handleSignIn)
	mux.HandleFunc("/api/v1/auth/verify", handleVerify)
	mux.HandleFunc("/api/v1/auth/health", handleHealth)
	mux.HandleFunc("/health", handleHealth)

	log.Printf("[✓] Go Auth Microservice listening on :%s\n", port)
	if err := http.ListenAndServe(":"+port, mux); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}
