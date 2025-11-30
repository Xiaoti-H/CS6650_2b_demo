"""
Locust Load Testing Script for Product API
Tests both LocalStack and AWS deployments under various load conditions
"""

from locust import HttpUser, task, between, events
import random
import json
import time
from datetime import datetime

# Search terms to use in tests
SEARCH_TERMS = ["alpha", "beta", "gamma", "delta", "epsilon", "electronics", "sku"]
PRODUCT_IDS = [1, 100, 1000, 5000, 7000]

class ProductAPIUser(HttpUser):
    """
    Simulates a user accessing the Product API
    """
    # Wait between 1-3 seconds between tasks (simulates real user behavior)
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts"""
        # Test health check on startup
        self.client.get("/health")
    
    @task(10)  # Weight: 10 (most common operation)
    def search_products_small_limit(self):
        """Search products with small limit (typical query)"""
        query = random.choice(SEARCH_TERMS)
        self.client.get(
            "/products/search",
            params={"q": query, "limit": 100},
            name="/products/search?limit=100"
        )
    
    @task(5)  # Weight: 5
    def search_products_medium_limit(self):
        """Search products with medium limit"""
        query = random.choice(SEARCH_TERMS)
        self.client.get(
            "/products/search",
            params={"q": query, "limit": 1000},
            name="/products/search?limit=1000"
        )
    
    @task(2)  # Weight: 2
    def search_products_large_limit(self):
        """Search products with large limit"""
        query = random.choice(SEARCH_TERMS)
        self.client.get(
            "/products/search",
            params={"q": query, "limit": 5000},
            name="/products/search?limit=5000"
        )
    
    @task(3)  # Weight: 3
    def get_product_by_id(self):
        """Get a specific product by ID"""
        product_id = random.choice(PRODUCT_IDS)
        self.client.get(
            f"/products/{product_id}",
            name="/products/[id]"
        )
    
    @task(1)  # Weight: 1 (least common)
    def health_check(self):
        """Periodic health check"""
        self.client.get("/health")


# Custom statistics tracking
request_stats = {
    "localstack": [],
    "aws": []
}

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track individual request metrics"""
    if exception:
        return
    
    # Determine environment based on response time (rough heuristic)
    env = "aws" if response_time > 50 else "localstack"
    request_stats[env].append({
        "name": name,
        "response_time": response_time,
        "timestamp": time.time()
    })

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Generate summary report when test completes"""
    print("\n" + "="*60)
    print("LOCUST TEST SUMMARY")
    print("="*60)
    
    stats = environment.stats
    
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Average Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min Response Time: {stats.total.min_response_time}ms")
    print(f"Max Response Time: {stats.total.max_response_time}ms")
    
    print(f"\nPercentiles:")
    print(f"  50th percentile: {stats.total.get_response_time_percentile(0.5):.2f}ms")
    print(f"  75th percentile: {stats.total.get_response_time_percentile(0.75):.2f}ms")
    print(f"  95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"  99th percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    
    print(f"\nRequests per second: {stats.total.total_rps:.2f}")
    
    # Save detailed results to JSON
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_requests": stats.total.num_requests,
        "total_failures": stats.total.num_failures,
        "avg_response_time": stats.total.avg_response_time,
        "min_response_time": stats.total.min_response_time,
        "max_response_time": stats.total.max_response_time,
        "percentiles": {
            "p50": stats.total.get_response_time_percentile(0.5),
            "p75": stats.total.get_response_time_percentile(0.75),
            "p95": stats.total.get_response_time_percentile(0.95),
            "p99": stats.total.get_response_time_percentile(0.99),
        },
        "rps": stats.total.total_rps,
        "endpoints": {}
    }
    
    # Per-endpoint statistics
    for name, stat in stats.entries.items():
        results["endpoints"][name] = {
            "requests": stat.num_requests,
            "failures": stat.num_failures,
            "avg_response_time": stat.avg_response_time,
            "min_response_time": stat.min_response_time,
            "max_response_time": stat.max_response_time,
        }
    
    # Determine environment based on response times
    if stats.total.avg_response_time < 10:
        env_name = "localstack"
    else:
        env_name = "aws"
    
    filename = f"locust_results_{env_name}_{int(time.time())}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Detailed results saved to: {filename}")
    print("="*60 + "\n")