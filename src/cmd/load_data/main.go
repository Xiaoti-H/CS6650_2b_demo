package main

import (
	"context"
	"fmt"
	"os"
	"time"

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb"

	"HW5/internal"
	"HW5/internal/api"
)

func main() {
	tableName := os.Getenv("DYNAMODB_TABLE")
	if tableName == "" {
		tableName = "products"
	}

	fmt.Printf("🗄️  Loading data to DynamoDB table: %s\n", tableName)

	// Load AWS config
	cfg, err := config.LoadDefaultConfig(context.Background())
	if err != nil {
		fmt.Printf("❌ Failed to load AWS config: %v\n", err)
		os.Exit(1)
	}

	client := dynamodb.NewFromConfig(cfg)
	store := internal.NewDynamoDBStore(client, tableName)

	// Generate 10,000 products
	categories := []string{"Electronics", "Books", "Home", "Sports", "Toys"}
	brands := []string{"Alpha", "Beta", "Gamma", "Delta", "Epsilon"}

	products := make([]api.Product, 10000)
	for i := 0; i < 10000; i++ {
		brandIdx := i % len(brands)
		categoryIdx := i % len(categories)

		products[i] = api.Product{
			ProductId:    int32(i + 1),
			Sku:          fmt.Sprintf("SKU-%s-%d", brands[brandIdx], i+1),
			Manufacturer: brands[brandIdx] + " Company",
			CategoryId:   int32(categoryIdx + 1),
			Weight:       int32(i % 1000),
			SomeOtherId:  int32((i % 100) + 1),
		}
	}

	fmt.Println("Generated 10,000 products")

	// Batch write to DynamoDB
	fmt.Println("Starting batch upload to DynamoDB...")
	startTime := time.Now()

	err = store.BatchPut(products)
	if err != nil {
		fmt.Printf("❌ Failed to batch write: %v\n", err)
		os.Exit(1)
	}

	loadTime := time.Since(startTime)
	fmt.Printf("✅ Successfully loaded 10,000 products in %.2f seconds\n", loadTime.Seconds())

	// Verify count
	count, err := store.CountItems()
	if err != nil {
		fmt.Printf("⚠️  Warning: Could not verify count: %v\n", err)
	} else {
		fmt.Printf("✅ Verified: DynamoDB table contains %d products\n", count)
	}
}
