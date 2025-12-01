#!/usr/bin/env python3
"""
Load 10,000 products into LocalStack DynamoDB
"""

import boto3
import sys

# LocalStack configuration
endpoint_url = "http://localhost:4566"
table_name = "products"
region = "us-east-1"

print("="*60)
print("Loading Products into LocalStack DynamoDB")
print("="*60)
print(f"Endpoint: {endpoint_url}")
print(f"Table: {table_name}")
print()

# Create DynamoDB client
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url=endpoint_url,
    region_name=region,
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

table = dynamodb.Table(table_name)

# Generate products
brands = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
categories = [1, 2, 3, 4, 5]

total_products = 10000
print(f"Loading {total_products} products...")
print()

count = 0
errors = 0

# Batch write items
with table.batch_writer() as batch:
    for i in range(1, total_products + 1):
        brand_idx = i % len(brands)
        category_idx = i % len(categories)
        
        try:
            product = {
                'product_id': i,
                'sku': f"SKU-{brands[brand_idx]}-{i}",
                'manufacturer': f"{brands[brand_idx]} Company",
                'category_id': categories[category_idx],
                'weight': i % 1000,
                'some_other_id': (i % 100) + 1,
                # Add lowercase fields for case-insensitive search
                'lower_sku': f"sku-{brands[brand_idx]}-{i}".lower(),
                'lower_manufacturer': f"{brands[brand_idx]} company".lower()
            }
            
            batch.put_item(Item=product)
            count += 1
            
            if i % 1000 == 0:
                print(f"  Loaded {i}/{total_products} products...")
                
        except Exception as e:
            errors += 1
            if errors < 5:  # Only print first few errors
                print(f"  Error loading product {i}: {e}")

print()
print(f"✅ Successfully loaded {count} products!")
if errors > 0:
    print(f"⚠️  {errors} errors occurred")
print()

# Verify count
print("Verifying data...")
try:
    response = table.scan(Select='COUNT')
    actual_count = response['Count']
    print(f"✅ Table contains {actual_count} items")
except Exception as e:
    print(f"❌ Error verifying: {e}")

print()
print("="*60)
print("Data loading complete!")
print("="*60)