"""
Sample Data Generator for Smart Price Predictor
Generates realistic product price data for testing
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_sample_data(num_products=50, days=180, output_file='data.csv'):
    """
    Generate sample e-commerce data.
    
    Args:
        num_products: Number of unique products
        days: Number of days of historical data
        output_file: Output CSV filename
    """
    
    # Product categories and names
    products = [
        # Electronics
        "Apple iPhone 15 Pro Max 256GB",
        "Samsung Galaxy S24 Ultra 5G",
        "Sony WH-1000XM5 Wireless Headphones",
        "iPad Pro 12.9 inch M2 Chip",
        "MacBook Air M2 13 inch",
        "Dell XPS 15 Laptop",
        "Logitech MX Master 3S Mouse",
        "Canon EOS R6 Camera",
        "Bose QuietComfort Earbuds II",
        "Apple Watch Series 9",
        
        # Home & Kitchen
        "Instant Pot Duo Plus 9-in-1",
        "Dyson V15 Detect Vacuum",
        "Philips Air Fryer XXL",
        "Ninja Professional Blender",
        "KitchenAid Stand Mixer",
        "Keurig K-Elite Coffee Maker",
        "Samsung Smart Refrigerator",
        "LG Washing Machine Front Load",
        "Cuisinart Food Processor",
        "Roomba i7+ Robot Vacuum",
        
        # Fashion
        "Nike Air Max 270 Running Shoes",
        "Adidas Ultraboost 22 Sneakers",
        "Levi's 501 Original Jeans",
        "The North Face Jacket",
        "Ray-Ban Aviator Sunglasses",
        "Fossil Gen 6 Smartwatch",
        "Timex Weekender Watch",
        "Puma Running T-Shirt",
        "Under Armour Sports Backpack",
        "Herschel Supply Co Backpack",
        
        # Books & Stationery
        "Atomic Habits Hardcover Book",
        "The Psychology of Money",
        "Sapiens: A Brief History",
        "Moleskine Classic Notebook",
        "Parker Jotter Ballpoint Pen",
        "Leuchtturm1917 Bullet Journal",
        "Kindle Paperwhite E-reader",
        "Wacom Drawing Tablet",
        "HP DeskJet Printer",
        "Staedtler Pencil Set",
        
        # Sports & Fitness
        "Yoga Mat Premium Non-Slip",
        "Fitbit Charge 5 Tracker",
        "Dumbbells Set 20kg",
        "Resistance Bands Set",
        "Protein Powder Whey 2kg",
        "Running Water Bottle",
        "Gym Gloves Training",
        "Jump Rope Speed",
        "Foam Roller Massage",
        "Boxing Gloves Professional"
    ]
    
    # Base prices for products (in rupees)
    base_prices = {
        product: random.uniform(500, 80000) 
        for product in products[:num_products]
    }
    
    # Generate data
    data = []
    start_date = datetime.now() - timedelta(days=days)
    
    print(f"Generating {num_products} products over {days} days...")
    
    for product in list(base_prices.keys()):
        base_price = base_prices[product]
        
        # Determine trend (increasing, decreasing, or stable)
        trend = random.choice(['increasing', 'decreasing', 'stable', 'seasonal'])
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            
            # Skip some days randomly to make it realistic
            if random.random() < 0.3:  # 30% chance of no sale that day
                continue
            
            # Calculate price based on trend
            if trend == 'increasing':
                # Gradually increasing price
                trend_price = base_price + (day * base_price * 0.001)
            elif trend == 'decreasing':
                # Gradually decreasing price
                trend_price = base_price - (day * base_price * 0.001)
            elif trend == 'seasonal':
                # Seasonal variation (sine wave)
                seasonal_factor = np.sin(day / 30) * 0.1
                trend_price = base_price * (1 + seasonal_factor)
            else:
                # Stable with minor fluctuations
                trend_price = base_price
            
            # Add random daily fluctuation (±5%)
            daily_fluctuation = random.uniform(-0.05, 0.05)
            price = trend_price * (1 + daily_fluctuation)
            
            # Ensure price is positive
            price = max(price, base_price * 0.5)
            
            # Random number of sales per day
            num_sales = random.randint(1, 5)
            for _ in range(num_sales):
                data.append({
                    'InvoiceDate': current_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'Description': product,
                    'UnitPrice': round(price, 2)
                })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Shuffle data
    df = df.sample(frac=1).reset_index(drop=True)
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    
    print(f"\n✓ Generated {len(df)} records")
    print(f"✓ {df['Description'].nunique()} unique products")
    print(f"✓ Date range: {df['InvoiceDate'].min()} to {df['InvoiceDate'].max()}")
    print(f"✓ Saved to: {output_file}")
    
    # Print sample
    print("\nSample data:")
    print(df.head(10))
    
    # Print price statistics
    print("\nPrice statistics:")
    print(df.groupby('Description')['UnitPrice'].agg(['mean', 'min', 'max', 'count']).head())

if __name__ == "__main__":
    print("🔧 Sample Data Generator for Smart Price Predictor")
    print("=" * 60)
    
    # Generate data
    generate_sample_data(
        num_products=50,    # Number of products
        days=180,           # 6 months of data
        output_file='data.csv'
    )
    
    print("\n✅ Data generation complete!")
    print("\nNext steps:")
    print("  1. Run: python app.py")
    print("  2. Run: python test_system.py")
    print("  3. Open index.html in browser")
