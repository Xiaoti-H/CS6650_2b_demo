package internal

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/feature/dynamodb/attributevalue"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb/types"

	"HW5/internal/api"
)

// DynamoDBStore implements the Store interface using DynamoDB
type DynamoDBStore struct {
	client    *dynamodb.Client
	tableName string
}

// NewDynamoDBStore creates a new DynamoDB-backed store
func NewDynamoDBStore(client *dynamodb.Client, tableName string) *DynamoDBStore {
	return &DynamoDBStore{
		client:    client,
		tableName: tableName,
	}
}

// Get retrieves a product by ID from DynamoDB
func (s *DynamoDBStore) Get(id int32) (api.Product, bool) {
	ctx := context.Background()

	result, err := s.client.GetItem(ctx, &dynamodb.GetItemInput{
		TableName: aws.String(s.tableName),
		Key: map[string]types.AttributeValue{
			"product_id": &types.AttributeValueMemberN{Value: fmt.Sprintf("%d", id)},
		},
	})

	if err != nil || result.Item == nil {
		return api.Product{}, false
	}

	var product api.Product
	err = attributevalue.UnmarshalMap(result.Item, &product)
	if err != nil {
		return api.Product{}, false
	}

	return product, true
}

// Put adds or updates a product in DynamoDB
func (s *DynamoDBStore) Put(p api.Product) {
	ctx := context.Background()

	item, err := attributevalue.MarshalMap(p)
	if err != nil {
		fmt.Printf("Error marshaling product: %v\n", err)
		return
	}

	_, err = s.client.PutItem(ctx, &dynamodb.PutItemInput{
		TableName: aws.String(s.tableName),
		Item:      item,
	})

	if err != nil {
		fmt.Printf("Error putting item: %v\n", err)
	}
}

// Upsert adds or updates a product, returns true if created (new)
func (s *DynamoDBStore) Upsert(p api.Product) bool {
	// Check if exists first
	_, exists := s.Get(p.ProductId)
	s.Put(p)
	return !exists
}

// Search searches products in DynamoDB by SKU or Manufacturer
// This uses a Scan operation with filter expressions
// Note: Scan is expensive but necessary for text search without indexes
func (s *DynamoDBStore) Search(query string, limit int) ([]api.Product, int) {
	ctx := context.Background()
	query = strings.ToLower(query)

	// DynamoDB Scan with filter expression
	// We'll scan up to 'limit' items and filter by SKU or Manufacturer
	input := &dynamodb.ScanInput{
		TableName:        aws.String(s.tableName),
		Limit:            aws.Int32(int32(limit)),
		FilterExpression: aws.String("contains(lower_sku, :query) OR contains(lower_manufacturer, :query)"),
		ExpressionAttributeValues: map[string]types.AttributeValue{
			":query": &types.AttributeValueMemberS{Value: query},
		},
	}

	result, err := s.client.Scan(ctx, input)
	if err != nil {
		fmt.Printf("Error scanning: %v\n", err)
		return []api.Product{}, 0
	}

	var products []api.Product
	err = attributevalue.UnmarshalListOfMaps(result.Items, &products)
	if err != nil {
		fmt.Printf("Error unmarshaling: %v\n", err)
		return []api.Product{}, 0
	}

	// Return at most 20 results (matching the memory store behavior)
	if len(products) > 20 {
		products = products[:20]
	}

	return products, int(result.ScannedCount)
}

// BatchPut efficiently writes multiple products to DynamoDB
func (s *DynamoDBStore) BatchPut(products []api.Product) error {
	ctx := context.Background()

	// DynamoDB BatchWriteItem supports max 25 items per request
	batchSize := 25
	successCount := 0

	for i := 0; i < len(products); i += batchSize {
		end := i + batchSize
		if end > len(products) {
			end = len(products)
		}

		batch := products[i:end]
		writeRequests := make([]types.WriteRequest, len(batch))

		for j, p := range batch {
			item, err := attributevalue.MarshalMap(map[string]interface{}{
				"product_id":         p.ProductId,
				"sku":                p.Sku,
				"manufacturer":       p.Manufacturer,
				"category_id":        p.CategoryId,
				"weight":             p.Weight,
				"some_other_id":      p.SomeOtherId,
				"lower_sku":          strings.ToLower(p.Sku),
				"lower_manufacturer": strings.ToLower(p.Manufacturer),
			})
			if err != nil {
				return fmt.Errorf("marshal error: %w", err)
			}

			writeRequests[j] = types.WriteRequest{
				PutRequest: &types.PutRequest{Item: item},
			}
		}

		// Retry logic for unprocessed items
		maxRetries := 3
		unprocessedItems := writeRequests

		for retry := 0; retry < maxRetries && len(unprocessedItems) > 0; retry++ {
			output, err := s.client.BatchWriteItem(ctx, &dynamodb.BatchWriteItemInput{
				RequestItems: map[string][]types.WriteRequest{
					s.tableName: unprocessedItems,
				},
			})

			if err != nil {
				fmt.Printf("⚠️  Batch write error (retry %d/%d): %v\n", retry+1, maxRetries, err)
				time.Sleep(time.Second * time.Duration(retry+1)) // Exponential backoff
				continue
			}

			// Check for unprocessed items
			if len(output.UnprocessedItems) > 0 {
				unprocessedItems = output.UnprocessedItems[s.tableName]
				fmt.Printf("⚠️  %d unprocessed items, retrying...\n", len(unprocessedItems))
				time.Sleep(time.Second * time.Duration(retry+1))
			} else {
				unprocessedItems = nil
				successCount += len(batch)
			}
		}

		if len(unprocessedItems) > 0 {
			fmt.Printf("❌ Failed to write %d items after retries\n", len(unprocessedItems))
		}

		// Progress indicator
		if (i/batchSize)%10 == 0 {
			fmt.Printf("Loaded %d/%d products... (Success: %d)\n", end, len(products), successCount)
		}

		// Small delay to avoid throttling
		time.Sleep(time.Millisecond * 50)
	}

	fmt.Printf("\n📊 Total successfully written: %d/%d\n", successCount, len(products))
	return nil
}

// CountItems returns the total number of items in the table
func (s *DynamoDBStore) CountItems() (int, error) {
	ctx := context.Background()

	result, err := s.client.Scan(ctx, &dynamodb.ScanInput{
		TableName: aws.String(s.tableName),
		Select:    types.SelectCount,
	})

	if err != nil {
		return 0, err
	}

	return int(result.Count), nil
}
