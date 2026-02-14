"""
Demo Script - Test Enhanced Version with Real Product URLs
"""

import requests
import json

API_URL = "http://localhost:5000/api"

def test_product(name, url, source):
    """Test a specific product URL"""
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*70}")
    
    try:
        payload = {
            "url": url,
            "source": source,
            "productName": name,
            "productId": "test"
        }
        
        print("Sending request to API...")
        response = requests.post(
            f"{API_URL}/analyze",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✓ SUCCESS!")
            print(f"\n📦 PRODUCT INFO:")
            print(f"   Name: {data['product']['name']}")
            print(f"   Price: ₹{data['product']['current_price']:,.2f}")
            print(f"   Category: {data['product']['category']}")
            print(f"   Source: {data['product']['source']}")
            print(f"   Data: {data['product'].get('data_source', 'unknown')}")
            
            print(f"\n🔮 PREDICTIONS:")
            for period, price in data['predictions'].items():
                print(f"   {period}: ₹{price:,.2f}")
            
            print(f"\n💡 RECOMMENDATION:")
            rec = data['recommendation']
            print(f"   Action: {rec['action']}")
            print(f"   Confidence: {rec['confidence']*100:.1f}%")
            if rec['savings'] > 0:
                print(f"   Potential Savings: ₹{rec['savings']:,.2f}")
                print(f"   Best time: {rec['best_time_days']} days")
            
            print(f"\n📊 STATISTICS:")
            stats = data['statistics']
            for key, value in stats.items():
                if isinstance(value, float):
                    print(f"   {key}: ₹{value:,.2f}" if 'price' in key else f"   {key}: {value:.2f}")
                else:
                    print(f"   {key}: {value}")
            
            if data.get('disclaimer'):
                print(f"\n⚠️  {data['disclaimer']}")
            
            return True
        else:
            print(f"\n✗ FAILED: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to API server!")
        print("Make sure Flask server is running:")
        print("   python app_enhanced.py")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run demo tests"""
    print("\n" + "🚀 ENHANCED VERSION DEMO ".center(70, "="))
    print("Testing with real Amazon & Flipkart product URLs")
    print("="*70)
    
    # Test products
    test_cases = [
        {
            'name': 'iPhone 15 Pro Max',
            'url': 'https://www.amazon.in/Apple-iPhone-15-128-GB/dp/B0CHX1W1XY',
            'source': 'amazon'
        },
        {
            'name': 'Samsung Galaxy S24 Ultra',
            'url': 'https://www.amazon.in/Samsung-Galaxy-Ultra-Green-Storage/dp/B0CMDRCW3G',
            'source': 'amazon'
        },
        {
            'name': 'Sony Headphones',
            'url': 'https://www.amazon.in/Sony-WH-1000XM5-Cancelling-Headphones/dp/B0BZD3NZYL',
            'source': 'amazon'
        }
    ]
    
    # print("\n📝 Note: Web scraping may fail due to:")
    # print("   - Anti-bot protection")
    # print("   - Rate limiting")
    # print("   - Network issues")
    # print("\nIf scraping fails, the system will show an error message.")
    # print("This is expected behavior for a hackathon demo!")
    
    input("\n Press Enter to start testing... ")
    
    successful = 0
    for test in test_cases:
        if test_product(test['name'], test['url'], test['source']):
            successful += 1
        input("\nPress Enter for next test...")
    
    print(f"\n{'='*70}")
    print(f"RESULTS: {successful}/{len(test_cases)} successful")
    print(f"{'='*70}")
    
    if successful == 0:
        print("\n⚠️  Web scraping blocked by Amazon/Flipkart")
        # print("\nThis is normal! For hackathon demo:")
        # print("   1. Use the mock data in script.js")
        # print("   2. Or explain: 'In production, we'd use official APIs'")
        # print("   3. Show the intelligent prediction algorithm instead")
    else:
        print("\n✓ System is Ready!")

if __name__ == "__main__":
    main()
