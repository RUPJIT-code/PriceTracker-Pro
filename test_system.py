"""
Test Script for Smart Price Predictor
Run this to verify your setup is working correctly
"""

import requests
import json
import sys

API_URL = "http://localhost:5000/api"

def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def test_health():
    """Test health endpoint."""
    print_header("TEST 1: Health Check")
    try:
        response = requests.get(f"{API_URL}/health")
        data = response.json()
        print(f"✓ Status: {data['status']}")
        print(f"✓ Data loaded: {data['data_loaded']}")
        print(f"✓ Models cached: {data['models_loaded']}")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def test_products():
    """Test products endpoint."""
    print_header("TEST 2: Available Products")
    try:
        response = requests.get(f"{API_URL}/products")
        data = response.json()
        print(f"✓ Total products: {data['total_products']}")
        print("\nTop 5 products:")
        for i, product in enumerate(data['products'][:5], 1):
            print(f"  {i}. {product['name']} ({product['data_points']} records)")
        return data['products'][0]['name'] if data['products'] else None
    except Exception as e:
        print(f"✗ Failed: {e}")
        return None

def test_analyze(product_name):
    """Test analyze endpoint."""
    print_header("TEST 3: Product Analysis")
    try:
        payload = {
            "productName": product_name,
            "source": "test",
            "productId": "test123",
            "url": "http://test.com/product"
        }
        
        print(f"Analyzing: {product_name}")
        response = requests.post(
            f"{API_URL}/analyze",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 200:
            print(f"✗ Failed with status {response.status_code}")
            print(response.text)
            return False
        
        data = response.json()
        
        print(f"\n✓ Product: {data['product']['name']}")
        print(f"✓ Current Price: ₹{data['product']['current_price']:.2f}")
        print(f"✓ Recommendation: {data['recommendation']['action']}")
        
        print(f"\nPredictions:")
        for period, price in data['predictions'].items():
            print(f"  • {period}: ₹{price:.2f}")
        
        if data['recommendation']['action'] == 'WAIT':
            print(f"\nPotential Savings: ₹{data['recommendation']['savings']:.2f}")
            print(f"Best time to buy: {data['recommendation']['best_time_days']} days")
        
        print(f"\nStatistics:")
        print(f"  • Average Price: ₹{data['statistics']['avg_price']:.2f}")
        print(f"  • Min Price: ₹{data['statistics']['min_price']:.2f}")
        print(f"  • Max Price: ₹{data['statistics']['max_price']:.2f}")
        print(f"  • Volatility: {data['statistics']['volatility']}")
        print(f"  • Model R² Score: {data['statistics']['r2_score']:.2f}")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "🚀 SMART PRICE PREDICTOR - TEST SUITE ".center(60, "="))
    print("Make sure the Flask server is running on http://localhost:5000")
    print("=" * 60)
    
    # Test 1: Health
    if not test_health():
        print("\n❌ Server not responding. Please start the Flask server:")
        print("   python app.py")
        sys.exit(1)
    
    # Test 2: Products
    product_name = test_products()
    if not product_name:
        print("\n❌ No products available. Please check your data.csv file.")
        sys.exit(1)
    
    # Test 3: Analysis
    if not test_analyze(product_name):
        print("\n❌ Analysis failed.")
        sys.exit(1)
    
    # All tests passed
    print_header("✅ ALL TESTS PASSED!")
    print("\nYour system is working correctly! 🎉")
    print("\nNext steps:")
    print("  1. Open index.html in your browser")
    print("  2. Paste a product URL")
    print("  3. Click 'Analyze Price'")
    print("\nHappy hacking! 🚀")

if __name__ == "__main__":
    main()
