#!/usr/bin/env python3
"""
Simple Performance Test Script for Product API
Tests: LocalStack vs AWS deployments
"""

import requests
import time
import statistics
import json
from datetime import datetime

class PerformanceTester:
    def __init__(self, base_url, environment_name):
        self.base_url = base_url
        self.env_name = environment_name
        self.results = {
            "environment": environment_name,
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
    
    def test_health_check(self):
        """Test 1: Health check response time"""
        print(f"\n📊 Testing health endpoint...")
        latencies = []
        
        for i in range(10):
            start = time.time()
            response = requests.get(f"{self.base_url}/health")
            latency = (time.time() - start) * 1000  # Convert to ms
            latencies.append(latency)
            
            if i == 0:  # Print first response
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.json()}")
        
        self.results["tests"]["health_check"] = {
            "avg_latency_ms": statistics.mean(latencies),
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "p50_latency_ms": statistics.median(latencies),
        }
        
        print(f"   ✅ Average latency: {statistics.mean(latencies):.2f}ms")
    
    def test_search_query(self, query="alpha", num_requests=100):
        """Test 2: Search query performance"""
        print(f"\n🔍 Testing search queries (n={num_requests})...")
        latencies = []
        found_counts = []
        
        for i in range(num_requests):
            start = time.time()
            response = requests.get(
                f"{self.base_url}/products/search",
                params={"q": query, "limit": 100}
            )
            latency = (time.time() - start) * 1000
            latencies.append(latency)
            
            if response.status_code == 200:
                data = response.json()
                found_counts.append(data.get("total_found", 0))
            
            # Progress indicator
            if (i + 1) % 20 == 0:
                print(f"   Progress: {i+1}/{num_requests}")
        
        # Calculate percentiles
        sorted_latencies = sorted(latencies)
        p50 = sorted_latencies[len(sorted_latencies) // 2]
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        
        self.results["tests"]["search_query"] = {
            "query": query,
            "num_requests": num_requests,
            "avg_latency_ms": statistics.mean(latencies),
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "p50_latency_ms": p50,
            "p95_latency_ms": p95,
            "p99_latency_ms": p99,
            "avg_results_found": statistics.mean(found_counts) if found_counts else 0,
        }
        
        print(f"   ✅ Average latency: {statistics.mean(latencies):.2f}ms")
        print(f"   ✅ P50: {p50:.2f}ms, P95: {p95:.2f}ms, P99: {p99:.2f}ms")
    
    def test_different_search_terms(self):
        """Test 3: Different search terms"""
        print(f"\n🔤 Testing various search terms...")
        search_terms = ["alpha", "beta", "gamma", "electronics", "sku"]
        
        results = {}
        for term in search_terms:
            latencies = []
            for _ in range(20):
                start = time.time()
                response = requests.get(
                    f"{self.base_url}/products/search",
                    params={"q": term, "limit": 100}
                )
                latency = (time.time() - start) * 1000
                latencies.append(latency)
            
            results[term] = {
                "avg_latency_ms": statistics.mean(latencies),
                "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)]
            }
            print(f"   '{term}': {statistics.mean(latencies):.2f}ms")
        
        self.results["tests"]["different_terms"] = results
    
    def test_get_product(self):
        """Test 4: Get specific product by ID"""
        print(f"\n🔢 Testing get product by ID...")
        product_ids = [1, 100, 1000, 10000, 50000]
        latencies = []
        
        for pid in product_ids:
            start = time.time()
            response = requests.get(f"{self.base_url}/products/{pid}")
            latency = (time.time() - start) * 1000
            latencies.append(latency)
            
            if response.status_code == 200:
                print(f"   Product {pid}: {latency:.2f}ms ✅")
            else:
                print(f"   Product {pid}: {latency:.2f}ms ❌ (status: {response.status_code})")
        
        self.results["tests"]["get_product"] = {
            "avg_latency_ms": statistics.mean(latencies),
            "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)]
        }
    
    def run_all_tests(self):
        """Run all performance tests"""
        print(f"\n{'='*60}")
        print(f"🚀 Performance Testing: {self.env_name}")
        print(f"   Base URL: {self.base_url}")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        try:
            self.test_health_check()
            self.test_search_query()
            self.test_different_search_terms()
            self.test_get_product()
            
            # Save results
            filename = f"results_{self.env_name}_{int(time.time())}.json"
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            print(f"\n{'='*60}")
            print(f"✅ All tests completed!")
            print(f"📄 Results saved to: {filename}")
            print(f"{'='*60}\n")
            
            self.print_summary()
            
        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
    
    def print_summary(self):
        """Print a summary of results"""
        print("\n📊 SUMMARY")
        print("-" * 60)
        
        if "health_check" in self.results["tests"]:
            hc = self.results["tests"]["health_check"]
            print(f"Health Check:      {hc['avg_latency_ms']:.2f}ms avg")
        
        if "search_query" in self.results["tests"]:
            sq = self.results["tests"]["search_query"]
            print(f"Search Query:      {sq['avg_latency_ms']:.2f}ms avg")
            print(f"                   {sq['p50_latency_ms']:.2f}ms (P50)")
            print(f"                   {sq['p95_latency_ms']:.2f}ms (P95)")
            print(f"                   {sq['p99_latency_ms']:.2f}ms (P99)")
        
        if "get_product" in self.results["tests"]:
            gp = self.results["tests"]["get_product"]
            print(f"Get Product:       {gp['avg_latency_ms']:.2f}ms avg")
        
        print("-" * 60)

def main():
    """Main function to run tests"""
    print("""
╔════════════════════════════════════════════════════════════╗
║         Product API Performance Testing Tool              ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Test LocalStack deployment
    print("\n1️⃣  Testing LocalStack deployment...")
    localstack_tester = PerformanceTester(
        base_url="http://localhost:8080",
        environment_name="localstack"
    )
    localstack_tester.run_all_tests()
    
    print("\n2️⃣  Testing AWS deployment...")
    aws_tester = PerformanceTester(
        base_url="http://product-api-alb-1232737685.us-east-1.elb.amazonaws.com",
        environment_name="aws"
    )
    aws_tester.run_all_tests()
    
    print("\n✨ Testing complete! Check the results JSON files.\n")

if __name__ == "__main__":
    main()