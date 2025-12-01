package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb"
	"github.com/go-chi/chi/v5"

	"HW5/internal"
	"HW5/internal/api"
)

// Handler implementation
type Handler struct {
	api.Unimplemented
	store internal.ProductStore
}

func (h *Handler) HealthCheck(w http.ResponseWriter, r *http.Request) {
	storageType := os.Getenv("STORAGE_TYPE")
	if storageType == "" {
		storageType = "memory"
	}

	response := map[string]interface{}{
		"status":      "healthy",
		"timestamp":   time.Now().Format(time.RFC3339),
		"service":     "product-api",
		"storage":     storageType,
		"environment": getEnvironment(),
	}
	internal.WriteJSON(w, http.StatusOK, response)
}

func (h *Handler) SearchProducts(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("q")
	if query == "" {
		internal.WriteError(w, http.StatusBadRequest, "INVALID_INPUT",
			"query parameter 'q' is required", "")
		return
	}

	limit := 100
	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil && l > 0 && l <= 10000 {
			limit = l
		}
	}

	startTime := time.Now()
	results, checkedCount := h.store.Search(query, limit)
	searchTime := time.Since(startTime)

	response := map[string]interface{}{
		"products":      results,
		"total_found":   len(results),
		"checked_count": checkedCount,
		"search_time":   fmt.Sprintf("%.2fms", float64(searchTime.Microseconds())/1000.0),
		"query":         query,
		"environment":   getEnvironment(),
	}

	internal.WriteJSON(w, http.StatusOK, response)
}

func (h *Handler) GetProduct(w http.ResponseWriter, r *http.Request, productId int32) {
	if productId < 1 {
		internal.WriteError(w, http.StatusNotFound, "NOT_FOUND", "Product not found",
			fmt.Sprintf("productId=%d", productId))
		return
	}

	if p, ok := h.store.Get(productId); ok {
		internal.WriteJSON(w, http.StatusOK, p)
		return
	}

	internal.WriteError(w, http.StatusNotFound, "NOT_FOUND", "Product not found",
		fmt.Sprintf("productId=%d", productId))
}

func (h *Handler) AddProductDetails(w http.ResponseWriter, r *http.Request, productId int32) {
	if productId < 1 {
		internal.WriteError(w, http.StatusBadRequest, "INVALID_INPUT", "productId must be >= 1",
			fmt.Sprintf("productId=%d", productId))
		return
	}

	var p api.Product
	dec := json.NewDecoder(r.Body)
	dec.DisallowUnknownFields()
	if err := dec.Decode(&p); err != nil {
		internal.WriteError(w, http.StatusBadRequest, "INVALID_INPUT", "invalid JSON body", err.Error())
		return
	}

	if msg, ok := validateProduct(p); !ok {
		internal.WriteError(w, http.StatusBadRequest, "INVALID_INPUT", msg, "")
		return
	}

	if p.ProductId != productId {
		internal.WriteError(w, http.StatusBadRequest, "INVALID_INPUT",
			"product_id must equal path productId",
			fmt.Sprintf("path=%d, body=%d", productId, p.ProductId))
		return
	}

	created := h.store.Upsert(p)

	if created {
		w.Header().Set("Location", fmt.Sprintf("/products/%d", productId))
		w.WriteHeader(http.StatusCreated)
	} else {
		w.WriteHeader(http.StatusNoContent)
	}
}

func validateProduct(p api.Product) (string, bool) {
	if p.ProductId < 1 {
		return "product_id must be >= 1", false
	}
	if ln := len(p.Sku); ln < 1 || ln > 100 {
		return "sku length must be 1..100", false
	}
	if ln := len(p.Manufacturer); ln < 1 || ln > 200 {
		return "manufacturer length must be 1..200", false
	}
	if p.CategoryId < 1 {
		return "category_id must be >= 1", false
	}
	if p.Weight < 0 {
		return "weight must be >= 0", false
	}
	if p.SomeOtherId < 1 {
		return "some_other_id must be >= 1", false
	}
	return "", true
}

func getEnvironment() string {
	if os.Getenv("AWS_ENDPOINT_URL") != "" {
		return "localstack"
	}
	if os.Getenv("STORAGE_TYPE") == "dynamodb" {
		return "aws-cloud"
	}
	return "local-memory"
}

// 🔥 修复后的函数 - 支持 DynamoDB！
func initializeStore() internal.ProductStore {
	storageType := os.Getenv("STORAGE_TYPE")

	if storageType == "dynamodb" {
		fmt.Println("🗄️  Initializing DynamoDB store...")

		tableName := os.Getenv("DYNAMODB_TABLE")
		if tableName == "" {
			tableName = "products"
		}

		ctx := context.Background()
		cfg, err := config.LoadDefaultConfig(ctx)
		if err != nil {
			fmt.Printf("❌ Failed to load AWS config: %v\n", err)
			fmt.Println("Falling back to memory store...")
			return createMemoryStore()
		}

		// 🔥 关键：检查 LocalStack endpoint
		endpointURL := os.Getenv("AWS_ENDPOINT_URL")
		var client *dynamodb.Client

		if endpointURL != "" {
			// LocalStack configuration
			fmt.Printf("📍 Using LocalStack endpoint: %s\n", endpointURL)
			client = dynamodb.NewFromConfig(cfg, func(o *dynamodb.Options) {
				o.BaseEndpoint = &endpointURL
			})
		} else {
			// Regular AWS configuration
			fmt.Println("☁️  Using AWS DynamoDB")
			client = dynamodb.NewFromConfig(cfg)
		}

		store := internal.NewDynamoDBStore(client, tableName)

		count, err := store.CountItems()
		if err != nil {
			fmt.Printf("❌ Failed to connect to DynamoDB: %v\n", err)
			fmt.Println("Falling back to memory store...")
			return createMemoryStore()
		}

		environment := "AWS"
		if endpointURL != "" {
			environment = "LocalStack"
		}
		fmt.Printf("✅ Connected to %s DynamoDB table '%s' with %d products\n", environment, tableName, count)
		return store
	}

	// Default: use in-memory storage
	fmt.Println("💾 Using in-memory storage")
	return createMemoryStore()
}

func createMemoryStore() internal.ProductStore {
	st := internal.NewStore()

	categories := []string{"Electronics", "Books", "Home", "Sports", "Toys"}
	brands := []string{"Alpha", "Beta", "Gamma", "Delta", "Epsilon"}

	fmt.Println("Loading 10,000 products into memory...")
	startTime := time.Now()

	for i := 1; i <= 10000; i++ {
		brandIdx := i % len(brands)
		categoryIdx := i % len(categories)

		st.Put(api.Product{
			ProductId:    int32(i),
			Sku:          fmt.Sprintf("SKU-%s-%d", brands[brandIdx], i),
			Manufacturer: brands[brandIdx] + " Company",
			CategoryId:   int32(categoryIdx + 1),
			Weight:       int32(i % 1000),
			SomeOtherId:  int32((i % 100) + 1),
		})

		if i%2000 == 0 {
			fmt.Printf("  Loaded %d products...\n", i)
		}
	}

	loadTime := time.Since(startTime)
	fmt.Printf("✅ Loaded 10,000 products in %.2f seconds\n", loadTime.Seconds())

	return st
}

func main() {
	store := initializeStore()

	h := &Handler{store: store}
	r := chi.NewRouter()

	r.Get("/health", h.HealthCheck)
	r.Get("/products/search", h.SearchProducts)

	srv := api.HandlerWithOptions(h, api.ChiServerOptions{
		BaseRouter: r,
		ErrorHandlerFunc: func(w http.ResponseWriter, r *http.Request, err error) {
			if e, ok := err.(*api.InvalidParamFormatError); ok &&
				e.ParamName == "productId" &&
				r.Method == http.MethodGet &&
				strings.HasPrefix(r.URL.Path, "/products/") {
				internal.WriteError(w, http.StatusNotFound, "NOT_FOUND", "Product not found", "invalid productId")
				return
			}
			http.Error(w, err.Error(), http.StatusBadRequest)
		},
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	env := getEnvironment()
	storageType := os.Getenv("STORAGE_TYPE")
	if storageType == "" {
		storageType = "memory"
	}

	fmt.Println()
	fmt.Println("================================================")
	fmt.Printf("🚀 Product API Server\n")
	fmt.Println("================================================")
	fmt.Printf("Environment:  %s\n", env)
	fmt.Printf("Storage:      %s\n", storageType)
	fmt.Printf("Port:         %s\n", port)
	fmt.Println()
	fmt.Println("Endpoints:")
	fmt.Println("  GET  /health")
	fmt.Println("  GET  /products/search?q={query}&limit={limit}")
	fmt.Println("  GET  /products/{id}")
	fmt.Println("  POST /products/{id}/details")
	fmt.Println("================================================")
	fmt.Println()

	_ = http.ListenAndServe(":"+port, srv)
}
