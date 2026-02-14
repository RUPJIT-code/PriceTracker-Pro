# 🛒 Smart Price Predictor - AI-Powered Shopping Assistant

An intelligent price prediction system for Amazon & Flipkart products using Machine Learning. Predicts future prices and recommends the best time to buy!

## 🌟 Features

- ✅ **Smart URL Parsing** - Paste any Amazon/Flipkart product link
- ✅ **ML Price Prediction** - Linear Regression forecasting for 7, 15, and 30 days
- ✅ **Buy/Wait Recommendations** - AI-powered buying decisions
- ✅ **Beautiful UI** - Modern, responsive, dark-themed interface
- ✅ **Real-time Charts** - Interactive price trend visualization
- ✅ **Fallback Logic** - Uses category trends if product data unavailable
- ✅ **RESTful API** - Clean Flask backend with JSON responses

## 🏗️ Tech Stack

### Frontend
- HTML5, CSS3, JavaScript (Vanilla)
- Chart.js for data visualization
- Responsive design (mobile-friendly)

### Backend
- Python 3.8+
- Flask (REST API)
- Pandas (Data processing)
- Scikit-learn (ML models)
- NumPy (Numerical computing)

## 📦 Installation

### Prerequisites
```bash
# Python 3.8 or higher
python --version

# pip package manager
pip --version
```

### Step 1: Clone/Download the Project
```bash
# If using git
git clone <your-repo-url>
cd smart-price-predictor

# Or just download and extract the ZIP file
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Prepare Your Dataset
Place your CSV file as `data.csv` in the project root with these columns:
- `InvoiceDate` - Date of the record
- `Description` - Product name
- `UnitPrice` - Price of the product

**Example CSV structure:**
```csv
InvoiceDate,Description,UnitPrice
2024-01-01,WHITE HANGING HEART T-LIGHT HOLDER,2.55
2024-01-02,WHITE HANGING HEART T-LIGHT HOLDER,2.55
2024-01-03,JUMBO BAG RED RETROSPOT,1.95
```

## 🚀 Running the Application

### Step 1: Start the Backend Server
```bash
python app.py
```

You should see:
```
✓ Loaded 25000 records
✓ 3500 unique products
🚀 Starting Flask API Server...
📍 API will be available at http://localhost:5000
```

### Step 2: Open the Frontend
Simply open `index.html` in your web browser:

**Option A - Double Click:**
- Double-click `index.html` file
- Should open in your default browser

**Option B - Using Python HTTP Server:**
```bash
# In a new terminal, in the project directory
python -m http.server 8080
```
Then open: http://localhost:8080

### Step 3: Use the Application!
1. Paste an Amazon or Flipkart product URL
2. Click "Analyze Price"
3. Get predictions and recommendations!

## 📁 Project Structure

```
smart-price-predictor/
├── index.html          # Frontend UI
├── styles.css          # Styling
├── script.js           # Frontend logic + API integration
├── app.py              # Flask backend API
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── data.csv           # Your dataset (you provide this)
```

## 🔧 API Endpoints

### 1. Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "models_loaded": 10,
  "data_loaded": true
}
```

### 2. Analyze Product
```http
POST /api/analyze
Content-Type: application/json

{
  "productName": "iPhone 15 Pro Max",
  "source": "amazon",
  "productId": "B0CHX1W1XY",
  "url": "https://www.amazon.in/..."
}
```

**Response:**
```json
{
  "success": true,
  "product": {
    "name": "iPhone 15 Pro Max",
    "current_price": 45999.00,
    "source": "amazon",
    "category": "Electronics"
  },
  "predictions": {
    "7_days": 44500.00,
    "15_days": 43200.00,
    "30_days": 41800.00
  },
  "recommendation": {
    "action": "WAIT",
    "savings": 4199.00,
    "best_time_days": 30,
    "confidence": 0.85
  },
  "statistics": {
    "avg_price": 43500.00,
    "min_price": 39999.00,
    "max_price": 49999.00,
    "volatility": "Medium",
    "r2_score": 0.78
  }
}
```

### 3. Get Available Products
```http
GET /api/products
```

### 4. Initialize System (if needed)
```http
POST /api/initialize
Content-Type: application/json

{
  "filepath": "data.csv"
}
```

## 🎯 How It Works

### Backend ML Pipeline

1. **Data Preprocessing**
   - Load CSV with product history
   - Clean missing values and invalid prices
   - Convert dates to numerical format (days since start)
   - Aggregate by product and date

2. **Model Training**
   - Train Linear Regression per product
   - Formula: `Price = Slope × Days + Intercept`
   - Positive slope = price increasing
   - Negative slope = price decreasing

3. **Prediction**
   - Predict prices for 7, 15, 30 days ahead
   - Compare with current price
   - Calculate potential savings

4. **Recommendation Logic**
   ```python
   if predicted_price < current_price - threshold:
       return "WAIT - Price will drop"
   else:
       return "BUY NOW - Price stable/rising"
   ```

5. **Fallback Strategy**
   - If product not found → use category average
   - If category not found → return error with suggestions

### Frontend Flow

1. User pastes Amazon/Flipkart URL
2. JavaScript parses URL to extract:
   - Product name
   - Product ID
   - Source (Amazon/Flipkart)
3. Sends POST request to `/api/analyze`
4. Displays results with:
   - Recommendation card (BUY/WAIT)
   - Price predictions
   - Interactive chart
   - Statistics

## 🎨 Customization

### Change Color Scheme
Edit `styles.css` variables:
```css
:root {
    --primary: #6366f1;      /* Main color */
    --success: #10b981;      /* Buy now color */
    --warning: #f59e0b;      /* Wait color */
}
```

### Add More Prediction Days
In `app.py`, modify:
```python
predictions = predict_future_prices(model, current_day, future_days=[7, 15, 30, 60])
```

And in `script.js`, add:
```javascript
const timeframes = [
    { key: '7_days', label: '7 Days Ahead' },
    { key: '15_days', label: '15 Days Ahead' },
    { key: '30_days', label: '30 Days Ahead' },
    { key: '60_days', label: '60 Days Ahead' }
];
```

### Change Decision Threshold
In `app.py`:
```python
# Default is 5% price drop
recommendation = make_buying_decision(current_price, predictions, threshold=0.05)

# More aggressive (3% threshold)
recommendation = make_buying_decision(current_price, predictions, threshold=0.03)
```

## 🐛 Troubleshooting

### Issue: "CORS Error" in Browser Console
**Solution:** Make sure Flask-CORS is installed and the backend is running:
```bash
pip install flask-cors
python app.py
```

### Issue: "No data available for product"
**Solution:** 
1. Check your `data.csv` has the product
2. Try a different product name
3. The system will automatically fall back to category average

### Issue: Backend not loading data
**Solution:**
```bash
# Check if data.csv exists
ls data.csv

# Manually initialize via API
curl -X POST http://localhost:5000/api/initialize \
  -H "Content-Type: application/json" \
  -d '{"filepath": "data.csv"}'
```

### Issue: Chart not displaying
**Solution:** Make sure Chart.js CDN is accessible. Check browser console for errors.

## 📊 Sample Dataset

If you don't have a dataset, you can use the UCI Online Retail dataset:
1. Download from: https://archive.ics.uci.edu/ml/datasets/online+retail
2. Rename to `data.csv`
3. Ensure columns: `InvoiceDate`, `Description`, `UnitPrice`

## 🚧 Limitations & Future Improvements

### Current Limitations
- ⚠️ Requires historical price data in dataset
- ⚠️ Linear Regression assumes linear trends
- ⚠️ No real-time web scraping (uses historical data)
- ⚠️ Product matching is fuzzy (may not find exact matches)

### Future Enhancements
- [ ] Real-time price scraping from Amazon/Flipkart
- [ ] Advanced ML models (LSTM, ARIMA for time series)
- [ ] User accounts and price alerts
- [ ] Email notifications when prices drop
- [ ] Compare prices across multiple platforms
- [ ] Browser extension for one-click predictions
- [ ] Mobile app (React Native)

## 📝 License

This is a hackathon project for educational purposes. Feel free to use and modify!

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Submit a pull request

## 📧 Contact

For questions or issues, please open an issue on GitHub or contact the developer.

---

**Built with ❤️ for the hackathon** | Powered by Machine Learning & Python
