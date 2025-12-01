#!/usr/bin/env python3
"""
Performance Test Script for LocalStack Deployment
Matches the test scenarios from Final Mastery Report
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
    
    def test_health_check(self, num_requests=10):
        """Test 1: Health check (10 requests)"""
        print(f"\n📊 Test 1: Health Check ({num_requests} requests)")
        print("-" * 60)
        latencies = []
        
        for i in range(num_requests):
            start = time.time()
            response = requests.get(f"{self.base_url}/health")
            latency = (time.time() - start) * 1000
            latencies.append(latency)
            
            if i == 0:
                print(f"First response: {response.json()}")
        
        avg = statistics.mean(latencies)
        self.results["tests"]["health_check"] = {
            "num_requests": num_requests,
            "avg_latency_ms": avg,
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "p50_latency_ms": statistics.median(latencies),
        }
        
        print(f"✅ Average latency: {avg:.2f}ms")
    
    def test_search_query(self, query="alpha", limit=100, num_requests=100):
        """Test 2: Search query (100 requests with limit=100)"""
        print(f"\n🔍 Test 2: Search Query (query='{query}', limit={limit}, {num_requests} requests)")
        print("-" * 60)
        latencies = []
        found_counts = []
        
        for i in range(num_requests):
            start = time.time()
            response = requests.get(
                f"{self.base_url}/products/search",
                params={"q": query, "limit": limit}
            )
            latency = (time.time() - start) * 1000
            latencies.append(latency)
            
            if response.status_code == 200:
                data = response.json()
                found_counts.append(data.get("total_found", 0))
            
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i+1}/{num_requests}")
        
        sorted_latencies = sorted(latencies)
        avg = statistics.mean(latencies)
        p50 = sorted_latencies[len(sorted_latencies) // 2]
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        
        self.results["tests"]["search_query"] = {
            "query": query,
            "limit": limit,
            "num_requests": num_requests,
            "avg_latency_ms": avg,
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "median_ms": p50,
            "p50_latency_ms": p50,
            "p95_latency_ms": p95,
            "p99_latency_ms": p99,
            "avg_results_found": statistics.mean(found_counts) if found_counts else 0,
        }
        
        print(f"✅ Avg: {avg:.2f}ms | P50: {p50:.2f}ms | P95: {p95:.2f}ms | P99: {p99:.2f}ms")
    
    def test_different_search_terms(self):
        """Test 3: Different search terms (5 terms × 20 requests)"""
        print(f"\n📚 Test 3: Different Search Terms (5 terms × 20 requests)")
        print("-" * 60)
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
            
            avg = statistics.mean(latencies)
            p95 = sorted(latencies)[int(len(latencies) * 0.95)]
            
            results[term] = {
                "avg_latency_ms": avg,
                "p95_latency_ms": p95
            }
            print(f"  '{term}': {avg:.2f}ms (P95: {p95:.2f}ms)")
        
        self.results["tests"]["different_terms"] = results
    
    def test_get_product(self):
        """Test 4: Get product by ID (5 different IDs)"""
        print(f"\n🔢 Test 4: Get Product by ID (5 different IDs)")
        print("-" * 60)
        product_ids = [1, 100, 1000, 5000, 10000]
        latencies = []
        
        for pid in product_ids:
            start = time.time()
            response = requests.get(f"{self.base_url}/products/{pid}")
            latency = (time.time() - start) * 1000
            latencies.append(latency)
            
            if response.status_code == 200:
                print(f"  Product {pid}: {latency:.2f}ms ✅")
            else:
                print(f"  Product {pid}: {latency:.2f}ms ❌ (status: {response.status_code})")
        
        if latencies:
            avg = statistics.mean(latencies)
            p95 = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0]
            
            self.results["tests"]["get_product"] = {
                "avg_latency_ms": avg,
                "p95_latency_ms": p95
            }
            print(f"✅ Average: {avg:.2f}ms")
    
    def test_query_limits(self):
        """Test 5: Performance by query limit (100, 1000, 5000)"""
        print(f"\n📊 Test 5: Performance by Query Limit")
        print("-" * 60)
        limits = [100, 1000, 5000]
        results = {}
        
        for limit in limits:
            print(f"\n  Testing limit={limit}...")
            latencies = []
            
            for _ in range(20):
                start = time.time()
                response = requests.get(
                    f"{self.base_url}/products/search",
                    params={"q": "alpha", "limit": limit}
                )
                latency = (time.time() - start) * 1000
                latencies.append(latency)
            
            sorted_latencies = sorted(latencies)
            median = sorted_latencies[len(sorted_latencies) // 2]
            p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
            
            results[limit] = {
                "median_ms": median,
                "p95_ms": p95
            }
            print(f"    Median: {median:.2f}ms | P95: {p95:.2f}ms")
        
        self.results["tests"]["query_limits"] = results
    
    def run_all_tests(self):
        """Run all performance tests"""
        print("\n" + "="*70)
        print("  LocalStack Performance Testing")
        print("  Based on Final Mastery Report Test Scenarios")
        print("="*70)
        print(f"Base URL: {self.base_url}")
        print(f"Environment: {self.env_name}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        try:
            # Run all tests matching your report
            self.test_health_check(num_requests=10)
            self.test_search_query(query="alpha", limit=100, num_requests=100)
            self.test_different_search_terms()
            self.test_get_product()
            self.test_query_limits()
            
            # Save results
            filename = f"localstack_results_{int(time.time())}.json"
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            print("\n" + "="*70)
            print("✅ All tests completed!")
            print(f"💾 Results saved to: {filename}")
            print("="*70)
            
            self.print_summary()
            self.print_report_format()
            
        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()
    
    def print_summary(self):
        """Print summary matching report format"""
        print("\n" + "="*70)
        print("  SUMMARY (for Report)")
        print("="*70)
        
        tests = self.results["tests"]
        
        if "health_check" in tests:
            hc = tests["health_check"]
            print(f"\n📋 Health Check (10 requests):")
            print(f"  Average: {hc['avg_latency_ms']:.2f}ms")
        
        if "search_query" in tests:
            sq = tests["search_query"]
            print(f"\n📋 Search Query (100 requests, limit=100):")
            print(f"  Average:     {sq['avg_latency_ms']:.2f}ms")
            print(f"  P50 (Med):   {sq['p50_latency_ms']:.2f}ms")
            print(f"  P95:         {sq['p95_latency_ms']:.2f}ms")
            print(f"  P99:         {sq['p99_latency_ms']:.2f}ms")
        
        if "get_product" in tests:
            gp = tests["get_product"]
            print(f"\n📋 Get Product by ID:")
            print(f"  Average: {gp['avg_latency_ms']:.2f}ms")
        
        if "query_limits" in tests:
            ql = tests["query_limits"]
            print(f"\n📋 Performance by Query Limit:")
            print(f"  {'Limit':<10} {'Median':<15} {'P95':<15}")
            print(f"  {'-'*10} {'-'*15} {'-'*15}")
            for limit, data in ql.items():
                print(f"  {limit:<10} {data['median_ms']:<15.2f} {data['p95_ms']:<15.2f}")
        
        print("\n" + "="*70)
    
    def print_report_format(self):
        """Print numbers ready to copy to report"""
        print("\n" + "="*70)
        print("  📝 COPY TO REPORT")
        print("="*70)
        
        tests = self.results["tests"]
        
        print("\nOverall Performance Comparison Table:")
        print("-" * 70)
        
        if "health_check" in tests:
            hc = tests["health_check"]
            print(f"Health Check        | {hc['avg_latency_ms']:.2f}ms | AWS: 81.18ms  | Ratio: {81.18/hc['avg_latency_ms']:.1f}x")
        
        if "search_query" in tests:
            sq = tests["search_query"]
            print(f"Search -Average     | {sq['avg_latency_ms']:.2f}ms | AWS: 78.13ms  | Ratio: {78.13/sq['avg_latency_ms']:.1f}x")
            print(f"Search - P50(Med)   | {sq['p50_latency_ms']:.2f}ms | AWS: 73.78ms  | Ratio: {73.78/sq['p50_latency_ms']:.1f}x")
            print(f"Search -P95         | {sq['p95_latency_ms']:.2f}ms | AWS: 107.82ms | Ratio: {107.82/sq['p95_latency_ms']:.1f}x")
            print(f"Search -P99         | {sq['p99_latency_ms']:.2f}ms | AWS: 132.37ms | Ratio: {132.37/sq['p99_latency_ms']:.1f}x")
        
        if "get_product" in tests:
            gp = tests["get_product"]
            print(f"Get Product         | {gp['avg_latency_ms']:.2f}ms | AWS: 78.84ms  | Ratio: {78.84/gp['avg_latency_ms']:.1f}x")
        
        print("\nPerformance by Query Limit Table:")
        print("-" * 70)
        if "query_limits" in tests:
            ql = tests["query_limits"]
            print(f"{'Limit':<10} {'LocalStack Median':<20} {'AWS Median':<15} {'Difference':<15}")
            print("-" * 70)
            aws_medians = {100: 39, 1000: 47, 5000: 87}
            for limit, data in ql.items():
                aws_median = aws_medians.get(limit, 0)
                diff = aws_median - data['median_ms']
                print(f"{limit:<10} {data['median_ms']:<20.2f} {aws_median:<15}ms +{diff:.2f}ms")
        
        print("\n" + "="*70)
        print("✅ Copy these numbers to your Final Mastery report!")
        print("="*70)

def main():
    """Main function"""
    print("""
╔══════════════════════════════════════════════════════════╗
║     LocalStack Performance Test                          ║
║     Matching Final Mastery Report Test Scenarios         ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    base_url = "http://localhost:8080"
    
    # Verify LocalStack is accessible
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ LocalStack API is accessible at {base_url}")
            health_data = response.json()
            print(f"   Storage: {health_data.get('storage', 'unknown')}")
            print(f"   Environment: {health_data.get('environment', 'unknown')}")
        else:
            print(f"❌ LocalStack returned status {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to LocalStack: {e}")
        print("\nMake sure:")
        print("  1. LocalStack is running: localstack status")
        print("  2. Container is running: docker ps | grep product-api")
        print("  3. API is accessible: curl http://localhost:8080/health")
        return
    
    # Run tests
    tester = PerformanceTester(base_url, "localstack")
    tester.run_all_tests()
    
    print("\n✨ Testing complete!")
    print("📊 Results saved to JSON file")
    print("📝 Copy the numbers above to your report")
    print("\n🎯 Next: Update your Final Mastery report with LocalStack data\n")

if __name__ == "__main__":
    main()