
"""
Load 100,000 products into DynamoDB
For AWS Learner Lab deployment
"""

import boto3
import time
import json
from datetime import datetime
from decimal import Decimal

class ProductDataLoader:
    def __init__(self, table_name, region='us-east-1'):
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
        self.batch_size = 25  # DynamoDB batch write limit
        
    def generate_products(self, count=100000):
        """Generate product data matching the Go API structure"""
        categories = ["Electronics", "Books", "Home", "Sports", "Toys"]
        brands = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
        
        products = []
        for i in range(1, count + 1):
            brand_idx = i % len(brands)
            category_idx = i % len(categories)
            
            product = {
                'product_id': i,
                'sku': f"SKU-{brands[brand_idx]}-{i}",
                'manufacturer': f"{brands[brand_idx]} Company",
                'category_id': category_idx + 1,
                'weight': i % 1000,
                'some_other_id': (i % 100) + 1
            }
            products.append(product)
            
        return products
    
    def batch_write(self, items):
        """Write a batch of items to DynamoDB"""
        with self.table.batch_writer() as batch:
            for item in items:
                # Convert integers to Decimal for DynamoDB
                item_decimal = {
                    k: Decimal(str(v)) if isinstance(v, int) else v 
                    for k, v in item.items()
                }
                batch.put_item(Item=item_decimal)
    
    def load_data(self, product_count=100000):
        """Load all products in batches"""
        print(f"\n{'='*60}")
        print(f"Loading {product_count:,} products to DynamoDB")
        print(f"Table: {self.table.table_name}")
        print(f"{'='*60}\n")
        
        # Generate products
        print("📊 Generating product data...")
        products = self.generate_products(product_count)
        print(f"   ✅ Generated {len(products):,} products\n")
        
        # Load in batches
        start_time = time.time()
        total_batches = (len(products) + self.batch_size - 1) // self.batch_size
        
        print(f"📤 Loading data in {total_batches} batches (25 items each)...")
        
        for i in range(0, len(products), self.batch_size):
            batch = products[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            
            try:
                self.batch_write(batch)
                
                # Progress indicator
                if batch_num % 100 == 0 or batch_num == total_batches:
                    progress = (batch_num / total_batches) * 100
                    elapsed = time.time() - start_time
                    items_loaded = min(i + self.batch_size, len(products))
                    rate = items_loaded / elapsed if elapsed > 0 else 0
                    
                    print(f"   Progress: {items_loaded:,}/{len(products):,} "
                          f"({progress:.1f}%) - {rate:.0f} items/sec")
                    
            except Exception as e:
                print(f"\n❌ Error in batch {batch_num}: {e}")
                raise
        
        elapsed_time = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"✅ Successfully loaded {len(products):,} products!")
        print(f"⏱️  Time taken: {elapsed_time:.2f} seconds")
        print(f"📊 Average rate: {len(products)/elapsed_time:.0f} items/second")
        print(f"{'='*60}\n")
    
    def verify_data(self, sample_ids=[1, 100, 1000, 10000, 50000, 100000]):
        """Verify some sample products were loaded correctly"""
        print("\n🔍 Verifying data...")
        
        for product_id in sample_ids:
            try:
                response = self.table.get_item(
                    Key={'product_id': product_id}
                )
                if 'Item' in response:
                    print(f"   ✅ Product {product_id}: {response['Item']['sku']}")
                else:
                    print(f"   ❌ Product {product_id}: Not found")
            except Exception as e:
                print(f"   ❌ Product {product_id}: Error - {e}")
        
        print("")

def main():
    """Main function"""
    import sys
    
    print("""
╔════════════════════════════════════════════════════════╗
║   DynamoDB Data Loader                                 ║
║   Load 100,000 products for testing                    ║
╚════════════════════════════════════════════════════════╝
    """)
    
    # Get table name from command line or use default
    if len(sys.argv) > 1:
        table_name = sys.argv[1]
    else:
        # Try to get from terraform output
        try:
            import subprocess
            result = subprocess.run(
                ['terraform', 'output', '-raw', 'dynamodb_table_name'],
                cwd='terraform',
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                table_name = result.stdout.strip()
            else:
                table_name = "product-api-products"  # Default
        except:
            table_name = "product-api-products"  # Default
    
    print(f"📋 Configuration:")
    print(f"   Table: {table_name}")
    print(f"   Region: us-east-1")
    print(f"   Items: 100,000")
    print("")
    
    # Check AWS credentials
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        if credentials is None:
            print("❌ Error: AWS credentials not configured")
            print("\n   Please set AWS credentials:")
            print("   export AWS_ACCESS_KEY_ID=...")
            print("   export AWS_SECRET_ACCESS_KEY=...")
            print("   export AWS_SESSION_TOKEN=...")
            print("")
            sys.exit(1)
        print(f"✅ AWS credentials configured\n")
    except Exception as e:
        print(f"❌ Error checking credentials: {e}")
        sys.exit(1)
    
    # Confirm before loading
    print("⚠️  This will write 100,000 items to DynamoDB")
    print("   Estimated cost: ~$1.25 for initial load")
    print("   (Pay-per-request pricing)")
    print("")
    
    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled")
        sys.exit(0)
    
    # Load data
    try:
        loader = ProductDataLoader(table_name)
        loader.load_data(100000)
        loader.verify_data()
        
        print("✨ Data loading complete!")
        print("")
        print("📝 Next steps:")
        print("   1. Test the API with search queries")
        print("   2. Run performance tests: python3 performance_test.py")
        print("")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()