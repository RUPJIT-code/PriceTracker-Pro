// ==========================================
// CONFIGURATION
// ==========================================
const API_BASE_URL = 'http://localhost:5000/api';  // Update with your Flask API URL

// ==========================================
// URL PARSER - Extract product info from Amazon/Flipkart/Myntra links
// ==========================================
class ProductURLParser {
    static parse(url) {
        try {
            const urlObj = new URL(url);
            const hostname = urlObj.hostname.toLowerCase();
            
            if (hostname.includes('amazon') || hostname.includes('amzn.in')) {
                return this.parseAmazon(url, urlObj);
            } else if (hostname.includes('flipkart')) {
                return this.parseFlipkart(url, urlObj);
            } else if (hostname.includes('myntra')) {
                return this.parseMyntra(url, urlObj);
            } else {
                throw new Error('URL must be from Amazon, Flipkart, or Myntra');
            }
        } catch (error) {
            throw new Error('Invalid URL format. Please enter a valid Amazon, Flipkart, or Myntra product link.');
        }
    }
    
    static parseAmazon(url, urlObj) {
        // Amazon URL patterns:
        // https://www.amazon.in/product-name/dp/B08L5VFHQQ
        // https://www.amazon.com/product-name/dp/B08L5VFHQQ
        // https://amzn.in/d/xxxxxxxx (short links)
        // https://www.amazon.in/gp/product/B08L5VFHQQ
        
        const pathParts = urlObj.pathname.split('/');
        const dpIndex = pathParts.indexOf('dp');
        const gpIndex = pathParts.indexOf('product');
        const dIndex = pathParts.indexOf('d');
        const queryAsin = urlObj.searchParams.get('asin');
        
        // amzn.in short links
        if (urlObj.hostname.toLowerCase().includes('amzn.in') && dIndex !== -1 && dIndex + 1 < pathParts.length) {
            return {
                source: 'amazon',
                productId: pathParts[dIndex + 1],
                productName: 'Amazon Product',
                url: url
            };
        }
        
        // /dp/<asin>
        if (dpIndex !== -1 && dpIndex + 1 < pathParts.length) {
            const productId = pathParts[dpIndex + 1];
            const productName = pathParts[dpIndex - 1] ? 
                this.formatProductName(pathParts[dpIndex - 1]) : 
                'Amazon Product';
            
            return {
                source: 'amazon',
                productId: productId,
                productName: productName,
                url: url
            };
        }

        // /gp/product/<asin>
        if (gpIndex !== -1 && gpIndex + 1 < pathParts.length) {
            return {
                source: 'amazon',
                productId: pathParts[gpIndex + 1],
                productName: 'Amazon Product',
                url: url
            };
        }

        // ?asin=<asin>
        if (queryAsin) {
            return {
                source: 'amazon',
                productId: queryAsin,
                productName: 'Amazon Product',
                url: url
            };
        }

        // Last fallback for valid Amazon host
        const last = pathParts[pathParts.length - 1];
        if (last) {
            return {
                source: 'amazon',
                productId: last,
                productName: 'Amazon Product',
                url: url
            };
        }

        throw new Error('Invalid Amazon URL. Could not find product information.');
    }
    
    static parseFlipkart(url, urlObj) {
        // Flipkart URL patterns:
        // https://www.flipkart.com/product-name/p/itm123456
        // https://dl.flipkart.com/s/abc123 (short links)
        
        const pathParts = urlObj.pathname.split('/');
        const pIndex = pathParts.indexOf('p');
        const sIndex = pathParts.indexOf('s');
        const queryPid = urlObj.searchParams.get('pid');
        
        // Standard product URL
        if (pIndex !== -1 && pIndex + 1 < pathParts.length) {
            const productId = pathParts[pIndex + 1];
            const productName = pathParts[1] ? 
                this.formatProductName(pathParts[1]) : 
                'Flipkart Product';
            
            return {
                source: 'flipkart',
                productId: productId,
                productName: productName,
                url: url
            };
        }
        
        // Short links like /s/<token>
        if (sIndex !== -1 && sIndex + 1 < pathParts.length) {
            return {
                source: 'flipkart',
                productId: pathParts[sIndex + 1],
                productName: 'Flipkart Product',
                url: url
            };
        }

        // Some Flipkart URLs include PID in query params
        if (queryPid) {
            return {
                source: 'flipkart',
                productId: queryPid,
                productName: 'Flipkart Product',
                url: url
            };
        }

        // Last fallback for valid Flipkart host with unknown path format
        if (pathParts.length > 1 && pathParts[pathParts.length - 1]) {
            return {
                source: 'flipkart',
                productId: pathParts[pathParts.length - 1],
                productName: 'Flipkart Product',
                url: url
            };
        }

        throw new Error('Invalid Flipkart URL. Could not find product information.');
    }

    static parseMyntra(url, urlObj) {
        // Myntra URL patterns:
        // https://www.myntra.com/<slug>/<id>/buy
        // https://www.myntra.com/<slug>/<id>
        const pathParts = urlObj.pathname.split('/').filter(Boolean);
        const numericPart = pathParts.find(p => /^\d+$/.test(p));
        const slugPart = pathParts.find(p => !/^\d+$/.test(p) && p.toLowerCase() !== 'buy');

        return {
            source: 'myntra',
            productId: numericPart || (pathParts[pathParts.length - 1] || 'myntra'),
            productName: slugPart ? this.formatProductName(slugPart) : 'Myntra Product',
            url: url
        };
    }
    
    static formatProductName(slug) {
        // Convert URL slug to readable name
        return slug
            .replace(/-/g, ' ')
            .replace(/\+/g, ' ')
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
}

// ==========================================
// API CLIENT
// ==========================================
class PricePredictionAPI {
    static async analyzeProduct(productData) {
        try {
            const response = await fetch(`${API_BASE_URL}/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(productData)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to analyze product');
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
    
    // Mock data for demo (remove when real API is ready)
    static async mockAnalyzeProduct(productData) {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        const currentPrice = 45999 + Math.random() * 10000;
        const predictions = {
            '7_days': currentPrice - (Math.random() * 2000),
            '15_days': currentPrice - (Math.random() * 3000),
            '30_days': currentPrice - (Math.random() * 5000)
        };
        
        return {
            success: true,
            product: {
                name: productData.productName,
                current_price: currentPrice,
                source: productData.source,
                category: 'Electronics',
                image_url: 'https://via.placeholder.com/150'
            },
            predictions: predictions,
            recommendation: {
                action: predictions['30_days'] < currentPrice ? 'WAIT' : 'BUY_NOW',
                savings: Math.abs(currentPrice - predictions['30_days']),
                best_time_days: 30,
                confidence: 0.85
            },
            statistics: {
                avg_price: currentPrice - 1000,
                min_price: currentPrice - 5000,
                max_price: currentPrice + 2000,
                volatility: 'Medium',
                r2_score: 0.78
            }
        };
    }
}

// ==========================================
// UI CONTROLLER
// ==========================================
class UIController {
    constructor() {
        this.elements = {
            urlInput: document.getElementById('productUrl'),
            analyzeBtn: document.getElementById('analyzeBtn'),
            btnText: document.querySelector('.btn-text'),
            btnLoader: document.querySelector('.btn-loader'),
            errorMessage: document.getElementById('errorMessage'),
            productInfo: document.getElementById('productInfo'),
            resultsSection: document.getElementById('resultsSection'),
            productImage: document.getElementById('productImage'),
            productName: document.getElementById('productName'),
            productSource: document.getElementById('productSource'),
            productCategory: document.getElementById('productCategory'),
            currentPrice: document.getElementById('currentPrice'),
            marketplacePrices: document.getElementById('marketplacePrices'),
            recommendationContent: document.getElementById('recommendationContent'),
            predictionsList: document.getElementById('predictionsList'),
            statsContent: document.getElementById('statsContent')
        };
        
        this.chart = null;
        this.initializeEventListeners();
    }

    isLikelyUrl(value) {
        return /^(https?:\/\/)/i.test(value);
    }

    getSortedPredictionEntries(predictions) {
        return Object.entries(predictions)
            .filter(([key, value]) => key.endsWith('_days') && typeof value === 'number')
            .map(([key, value]) => {
                const days = parseInt(key.split('_')[0], 10);
                return { key, days, value };
            })
            .filter(item => !Number.isNaN(item.days))
            .sort((a, b) => a.days - b.days);
    }

    formatPredictionLabel(days, withAhead = true) {
        if (days === 7 || days === 15) {
            return withAhead ? `${days} Days Ahead` : `${days} Days`;
        }

        if (days % 30 === 0) {
            const months = Math.round(days / 30);
            const monthLabel = `${months} ${months === 1 ? 'Month' : 'Months'}`;
            return withAhead ? `${monthLabel} Ahead` : monthLabel;
        }

        return withAhead ? `${days} Days Ahead` : `${days} Days`;
    }
    
    initializeEventListeners() {
        // Analyze button click
        this.elements.analyzeBtn.addEventListener('click', () => this.handleAnalyze());
        
        // Enter key in input
        this.elements.urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleAnalyze();
        });
        
        // Example buttons
        document.querySelectorAll('.example-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.elements.urlInput.value = e.target.dataset.url;
                this.handleAnalyze();
            });
        });
        
        // Modal controls
        const aboutModal = document.getElementById('aboutModal');
        const aboutLink = document.getElementById('aboutLink');
        const modalClose = document.querySelector('.modal-close');
        
        aboutLink.addEventListener('click', (e) => {
            e.preventDefault();
            aboutModal.style.display = 'block';
        });
        
        modalClose.addEventListener('click', () => {
            aboutModal.style.display = 'none';
        });
        
        window.addEventListener('click', (e) => {
            if (e.target === aboutModal) {
                aboutModal.style.display = 'none';
            }
        });
    }
    
    async handleAnalyze() {
        const inputText = this.elements.urlInput.value.trim();
        
        if (!inputText) {
            this.showError('Please enter a product URL or product name');
            return;
        }
        
        try {
            this.hideError();
            this.setLoading(true);
            
            let productData;
            if (this.isLikelyUrl(inputText)) {
                productData = ProductURLParser.parse(inputText);
            } else {
                // Product-name mode (no URL)
                productData = {
                    source: 'query',
                    productId: 'query',
                    productName: inputText,
                    url: ''
                };
            }
            console.log('Parsed product data:', productData);
            
            // Call API
            const result = await PricePredictionAPI.analyzeProduct(productData);
            
            // Display results
            this.displayResults(result);
            
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.setLoading(false);
        }
    }
    
    displayResults(data) {
        // Display product info
        this.elements.productName.textContent = data.product.name;
        this.elements.productSource.textContent = data.product.source.toUpperCase();
        this.elements.productCategory.textContent = data.product.category;
        this.elements.currentPrice.textContent = this.formatCurrency(data.product.current_price);
        this.elements.productImage.src = data.product.image_url;
        this.renderMarketplacePrices(data.product.marketplace_prices || {});
        
        // Show sections
        this.elements.productInfo.style.display = 'block';
        this.elements.resultsSection.style.display = 'block';
        
        // Display recommendation
        this.displayRecommendation(data.recommendation, data.product.current_price);
        
        // Display predictions
        this.displayPredictions(data.predictions, data.product.current_price);
        
        // Display statistics
        this.displayStatistics(data.statistics);
        
        // Draw chart
        this.drawPriceChart(data.product.current_price, data.predictions);
        
        // Smooth scroll to results
        setTimeout(() => {
            this.elements.productInfo.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }

    renderMarketplacePrices(prices) {
        if (!this.elements.marketplacePrices) return;

        const amazonPrice = prices.amazon;
        const flipkartPrice = prices.flipkart;
        const hasAny = (typeof amazonPrice === 'number' && amazonPrice > 0) ||
            (typeof flipkartPrice === 'number' && flipkartPrice > 0);

        if (!hasAny) {
            this.elements.marketplacePrices.innerHTML = '';
            return;
        }

        const formatOrNA = (value) => (typeof value === 'number' && value > 0)
            ? this.formatCurrency(value)
            : 'N/A';

        this.elements.marketplacePrices.innerHTML = `
            <div class="marketplace-price-chip amazon">
                <span class="marketplace-label">Amazon</span>
                <span class="marketplace-value">${formatOrNA(amazonPrice)}</span>
            </div>
            <div class="marketplace-price-chip flipkart">
                <span class="marketplace-label">Flipkart</span>
                <span class="marketplace-value">${formatOrNA(flipkartPrice)}</span>
            </div>
        `;
    }
    
    displayRecommendation(recommendation, currentPrice) {
        const isWait = recommendation.action === 'WAIT';
        
        const html = `
            <div class="recommendation-icon">${isWait ? '⏳' : '🛒'}</div>
            <h2 class="recommendation-title">${isWait ? 'WAIT' : 'BUY NOW'}</h2>
            <p class="recommendation-subtitle">
                ${isWait ? 
                    `Price is likely to drop in the next ${recommendation.best_time_days} days` : 
                    'Current price is favorable - recommended to purchase now'
                }
            </p>
            ${isWait ? `
                <div class="savings-info">
                    <span class="savings-amount">${this.formatCurrency(recommendation.savings)}</span>
                    <span class="savings-label">Potential Savings (${((recommendation.savings / currentPrice) * 100).toFixed(1)}%)</span>
                </div>
            ` : ''}
            <div class="savings-info">
                <span class="savings-label">Prediction Confidence</span>
                <span class="savings-amount">${(recommendation.confidence * 100).toFixed(0)}%</span>
            </div>
        `;
        
        this.elements.recommendationContent.innerHTML = html;
        
        // Update card styling
        const recCard = this.elements.recommendationContent.closest('.recommendation-card');
        if (isWait) {
            recCard.classList.add('wait');
        } else {
            recCard.classList.remove('wait');
        }
    }
    
    displayPredictions(predictions, currentPrice) {
        const timeframes = this.getSortedPredictionEntries(predictions)
            .map(item => ({ key: item.key, label: this.formatPredictionLabel(item.days, true) }));
        
        const html = timeframes.map(tf => {
            const price = predictions[tf.key];
            const change = price - currentPrice;
            const changePercent = ((change / currentPrice) * 100).toFixed(1);
            const isPositive = change > 0;
            
            return `
                <div class="prediction-item">
                    <div>
                        <div class="prediction-timeframe">${tf.label}</div>
                    </div>
                    <div style="text-align: right;">
                        <span class="prediction-price">${this.formatCurrency(price)}</span>
                        <span class="prediction-change ${isPositive ? 'positive' : 'negative'}">
                            ${isPositive ? '+' : ''}${changePercent}%
                        </span>
                    </div>
                </div>
            `;
        }).join('');
        
        this.elements.predictionsList.innerHTML = html;
    }
    
    displayStatistics(stats) {
        const trendMap = { increasing: 'Up', decreasing: 'Down' };
        const trendLabel = trendMap[(stats.trend || '').toLowerCase()] || 'Stable';

        const html = `
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-value">${this.formatCompactCurrency(stats.avg_price)}</span>
                    <span class="stat-label">Average Price</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${this.formatCompactCurrency(stats.min_price)}</span>
                    <span class="stat-label">Minimum Price</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${this.formatCompactCurrency(stats.max_price)}</span>
                    <span class="stat-label">Maximum Price</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${stats.volatility}</span>
                    <span class="stat-label">Price Volatility</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${(stats.r2_score * 100).toFixed(0)}%</span>
                    <span class="stat-label">Model Accuracy</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${trendLabel}</span>
                    <span class="stat-label">Price Trend</span>
                </div>
            </div>
        `;
        
        this.elements.statsContent.innerHTML = html;
    }

    formatCompactCurrency(amount) {
        if (typeof amount !== 'number' || Number.isNaN(amount)) return 'N/A';

        if (Math.abs(amount) >= 1000) {
            return '₹' + amount.toLocaleString('en-IN', {
                notation: 'compact',
                compactDisplay: 'short',
                maximumFractionDigits: 1
            }).toUpperCase();
        }

        return '₹' + amount.toLocaleString('en-IN', {
            maximumFractionDigits: 0
        });
    }
    
    drawPriceChart(currentPrice, predictions) {
        const ctx = document.getElementById('priceChart').getContext('2d');
        
        // Destroy existing chart if exists
        if (this.chart) {
            this.chart.destroy();
        }
        
        const sortedPredictions = this.getSortedPredictionEntries(predictions);
        const labels = ['Today', ...sortedPredictions.map(item => this.formatPredictionLabel(item.days, false))];
        const data = [currentPrice, ...sortedPredictions.map(item => item.value)];
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Predicted Price',
                    data: data,
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    pointBackgroundColor: '#6366f1',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f1f5f9',
                        bodyColor: '#f1f5f9',
                        borderColor: '#334155',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            label: (context) => {
                                return 'Price: ' + this.formatCurrency(context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: '#334155'
                        },
                        ticks: {
                            color: '#94a3b8',
                            callback: (value) => {
                                return '₹' + (value / 1000).toFixed(0) + 'k';
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: '#334155'
                        },
                        ticks: {
                            color: '#94a3b8'
                        }
                    }
                }
            }
        });
    }
    
    formatCurrency(amount) {
        return '₹' + amount.toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }
    
    setLoading(isLoading) {
        this.elements.analyzeBtn.disabled = isLoading;
        this.elements.btnText.style.display = isLoading ? 'none' : 'inline';
        this.elements.btnLoader.style.display = isLoading ? 'inline-block' : 'none';
        
        if (isLoading) {
            this.elements.productInfo.style.display = 'none';
            this.elements.resultsSection.style.display = 'none';
        }
    }
    
    showError(message) {
        this.elements.errorMessage.textContent = message;
        this.elements.errorMessage.style.display = 'flex';
    }
    
    hideError() {
        this.elements.errorMessage.style.display = 'none';
    }
}

// ==========================================
// INITIALIZE APP
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    const app = new UIController();
    console.log('Smart Price Predictor initialized!');
});
