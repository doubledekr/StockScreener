document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const refreshBtn = document.getElementById('refresh-btn');
    const loadingContainer = document.getElementById('loading-container');
    const errorContainer = document.getElementById('error-container');
    const errorMessage = document.getElementById('error-message');
    const stocksContainer = document.getElementById('stocks-container');
    const noResults = document.getElementById('no-results');
    
    // Market movers elements
    const marketMoversLoading = document.getElementById('market-movers-loading');
    const marketMoversError = document.getElementById('market-movers-error');
    const marketMoversTable = document.getElementById('market-movers-table');
    const marketMoversBody = document.getElementById('market-movers-body');
    
    // Modal elements
    const stockDetailModal = document.getElementById('stockDetailModal');
    const modalLoading = document.getElementById('modal-loading');
    const modalContent = document.getElementById('modal-content');
    const modalStockName = document.getElementById('modal-stock-name');
    const modalStockSymbol = document.getElementById('modal-stock-symbol');
    const technicalMetrics = document.getElementById('technical-metrics');
    const fundamentalMetrics = document.getElementById('fundamental-metrics');
    
    // Initialize Bootstrap modal
    const modal = new bootstrap.Modal(stockDetailModal);
    
    // Format numbers nicely
    function formatNumber(num, decimals = 2) {
        if (num === null || num === undefined) return 'N/A';
        return parseFloat(num).toFixed(decimals);
    }
    
    // Format percentages
    function formatPercent(num, decimals = 2) {
        if (num === null || num === undefined) return 'N/A';
        return `${parseFloat(num).toFixed(decimals)}%`;
    }
    
    // Create a row for metric tables
    function createMetricRow(label, value, isPositive = null) {
        let badgeClass = '';
        let badgeText = '';
        
        if (isPositive === true) {
            badgeClass = 'bg-success';
            badgeText = 'PASS';
        } else if (isPositive === false) {
            badgeClass = 'bg-danger';
            badgeText = 'FAIL';
        }
        
        let row = `<tr>
            <td>${label}</td>
            <td class="text-end">${value}`;
            
        if (badgeText) {
            row += ` <span class="badge ${badgeClass} ms-2">${badgeText}</span>`;
        }
        
        row += `</td></tr>`;
        return row;
    }
    
    // Create a stock card element
    function createStockCard(stock) {
        const card = document.createElement('div');
        card.className = 'col-lg-6 mb-4';
        
        // Calculate percentage above SMA200
        const percentAboveSMA200 = ((stock.technical_data.current_price / stock.technical_data.sma200) - 1) * 100;
        
        card.innerHTML = `
            <div class="card h-100">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">${stock.symbol}</h5>
                    <span class="badge bg-primary">${formatPercent(percentAboveSMA200, 1)} > SMA200</span>
                </div>
                <div class="card-body">
                    <div class="d-flex justify-content-between mb-3">
                        <div>
                            <h6 class="card-subtitle text-muted mb-2">${stock.company_name}</h6>
                            <h5 class="mb-0">$${formatNumber(stock.technical_data.current_price)}</h5>
                        </div>
                        <div class="mini-chart-container" style="width: 100px; height: 40px;">
                            <canvas id="miniChart-${stock.symbol}"></canvas>
                        </div>
                    </div>
                    
                    <div class="row mb-3">
                        <div class="col-6">
                            <div class="small text-muted">Quarterly Sales Growth</div>
                            <div class="${stock.fundamental_data.quarterly_sales_growth > 0 ? 'text-success' : 'text-danger'}">
                                ${formatPercent(stock.fundamental_data.quarterly_sales_growth)}
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="small text-muted">Quarterly EPS Growth</div>
                            <div class="${stock.fundamental_data.quarterly_eps_growth > 0 ? 'text-success' : 'text-danger'}">
                                ${formatPercent(stock.fundamental_data.quarterly_eps_growth)}
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-6">
                            <div class="small text-muted">Est. Sales Growth</div>
                            <div class="${stock.fundamental_data.estimated_sales_growth > 0 ? 'text-success' : 'text-danger'}">
                                ${formatPercent(stock.fundamental_data.estimated_sales_growth)}
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="small text-muted">Est. EPS Growth</div>
                            <div class="${stock.fundamental_data.estimated_eps_growth > 0 ? 'text-success' : 'text-danger'}">
                                ${formatPercent(stock.fundamental_data.estimated_eps_growth)}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card-footer">
                    <button class="btn btn-outline-primary btn-sm view-details" data-symbol="${stock.symbol}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-bar-chart-2 me-1">
                            <line x1="18" y1="20" x2="18" y2="10"></line>
                            <line x1="12" y1="20" x2="12" y2="4"></line>
                            <line x1="6" y1="20" x2="6" y2="14"></line>
                        </svg>
                        View Details
                    </button>
                </div>
            </div>
        `;
        
        return card;
    }
    
    // Display the stock detail modal
    function showStockDetail(symbol) {
        // Reset the modal
        modalLoading.classList.remove('d-none');
        modalContent.classList.add('d-none');
        technicalMetrics.innerHTML = '';
        fundamentalMetrics.innerHTML = '';
        
        // Show the modal
        modal.show();
        
        // Fetch the stock details
        fetch(`/api/stock/${symbol}`)
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    throw new Error(data.error || 'Failed to load stock details');
                }
                
                const stock = data.data;
                
                // Update modal content
                modalStockName.textContent = stock.company_name;
                modalStockSymbol.textContent = symbol;
                
                // Populate technical metrics
                technicalMetrics.innerHTML = `
                    ${createMetricRow('Current Price', `$${formatNumber(stock.technical_data.current_price)}`)}
                    ${createMetricRow('200-day SMA', `$${formatNumber(stock.technical_data.sma200)}`)}
                    ${createMetricRow('Price > SMA200', `${formatPercent(((stock.technical_data.current_price / stock.technical_data.sma200) - 1) * 100, 1)}`, stock.technical_data.price_above_sma200)}
                    ${createMetricRow('SMA200 Slope', formatNumber(stock.technical_data.sma200_slope, 4), stock.technical_data.sma200_slope_positive)}
                    ${createMetricRow('50-day SMA', `$${formatNumber(stock.technical_data.sma50)}`)}
                    ${createMetricRow('SMA50 > SMA200', `${formatPercent(((stock.technical_data.sma50 / stock.technical_data.sma200) - 1) * 100, 1)}`, stock.technical_data.sma50_above_sma200)}
                    ${createMetricRow('100-day SMA', `$${formatNumber(stock.technical_data.sma100)}`)}
                    ${createMetricRow('SMA100 > SMA200', `${formatPercent(((stock.technical_data.sma100 / stock.technical_data.sma200) - 1) * 100, 1)}`, stock.technical_data.sma100_above_sma200)}
                `;
                
                // Populate fundamental metrics
                fundamentalMetrics.innerHTML = `
                    ${createMetricRow('Quarterly Sales Growth', formatPercent(stock.fundamental_data.quarterly_sales_growth), stock.fundamental_data.quarterly_sales_growth_positive)}
                    ${createMetricRow('Quarterly EPS Growth', formatPercent(stock.fundamental_data.quarterly_eps_growth), stock.fundamental_data.quarterly_eps_growth_positive)}
                    ${createMetricRow('Est. Sales Growth (Year)', formatPercent(stock.fundamental_data.estimated_sales_growth), stock.fundamental_data.estimated_sales_growth_positive)}
                    ${createMetricRow('Est. EPS Growth (Year)', formatPercent(stock.fundamental_data.estimated_eps_growth), stock.fundamental_data.estimated_eps_growth_positive)}
                `;
                
                // Create the price chart
                if (stock.chart_data) {
                    createPriceChart('priceChart', stock.chart_data);
                }
                
                // Show the content
                modalLoading.classList.add('d-none');
                modalContent.classList.remove('d-none');
            })
            .catch(error => {
                console.error('Error fetching stock details:', error);
                modalLoading.classList.add('d-none');
                modalContent.classList.remove('d-none');
                modalStockName.textContent = 'Error Loading Data';
                modalStockSymbol.textContent = '';
                technicalMetrics.innerHTML = `<tr><td colspan="2" class="text-center text-danger">
                    Error loading stock details: ${error.message}
                </td></tr>`;
            });
    }
    
    // Database stats functions
    function loadDatabaseStats() {
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.stats) {
                    // Update cache info in UI if we have a stats section
                    const statsElement = document.getElementById('database-stats');
                    if (statsElement) {
                        const stats = data.stats;
                        let statsHtml = '';
                        
                        if (stats.last_screening_time) {
                            const lastScreeningDate = new Date(stats.last_screening_time);
                            const formattedDate = lastScreeningDate.toLocaleString();
                            statsHtml += `<div>Last updated: ${formattedDate}</div>`;
                        }
                        
                        if (stats.screening_result_count > 0) {
                            statsHtml += `<div>Saved stocks: ${stats.stock_count}</div>`;
                            statsHtml += `<div>Saved screenings: ${stats.screening_result_count}</div>`;
                        }
                        
                        if (stats.last_execution_time) {
                            statsHtml += `<div>Last scan duration: ${stats.last_execution_time.toFixed(1)}s</div>`;
                        }
                        
                        statsElement.innerHTML = statsHtml;
                        statsElement.classList.remove('d-none');
                    }
                }
            })
            .catch(error => {
                console.error('Error loading database stats:', error);
            });
    }
    
    // Clear database cache
    function clearDatabaseCache(days = 7) {
        fetch(`/api/cache/clear?days=${days}`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log(data.message);
                    // Refresh stats after clearing cache
                    loadDatabaseStats();
                }
            })
            .catch(error => {
                console.error('Error clearing cache:', error);
            });
    }
    
    // Load stock data from the API
    function loadStockData(useCache = true) {
        // Show loading state
        loadingContainer.classList.remove('d-none');
        stocksContainer.innerHTML = '';
        errorContainer.classList.add('d-none');
        noResults.classList.add('d-none');
        refreshBtn.disabled = true;
        
        // Fetch the data (with cache control)
        const cacheParam = useCache ? 'true' : 'false';
        fetch(`/api/screen?use_cache=${cacheParam}`)
            .then(response => response.json())
            .then(data => {
                // Hide loading state
                loadingContainer.classList.add('d-none');
                refreshBtn.disabled = false;
                
                // Check for success
                if (!data.success) {
                    throw new Error(data.error || 'Failed to screen stocks');
                }
                
                // Check if we have results
                if (!data.stocks || data.stocks.length === 0) {
                    noResults.classList.remove('d-none');
                    return;
                }
                
                // Render the stock cards
                data.stocks.forEach(stock => {
                    const card = createStockCard(stock);
                    stocksContainer.appendChild(card);
                    
                    // Create mini chart if we have chart data
                    if (stock.chart_data) {
                        setTimeout(() => {
                            createMiniChart(`miniChart-${stock.symbol}`, stock.chart_data);
                        }, 0);
                    }
                });
                
                // Add event listeners to view details buttons
                document.querySelectorAll('.view-details').forEach(button => {
                    button.addEventListener('click', function() {
                        const symbol = this.getAttribute('data-symbol');
                        showStockDetail(symbol);
                    });
                });
            })
            .catch(error => {
                // Show error state
                console.error('Error loading stock data:', error);
                loadingContainer.classList.add('d-none');
                errorContainer.classList.remove('d-none');
                errorMessage.textContent = error.message;
                refreshBtn.disabled = false;
            });
    }
    
    // Add event listeners
    refreshBtn.addEventListener('click', function() {
        // Force refresh from API (no cache)
        loadStockData(false);
    });
    
    // Add event listener to cache control if it exists
    const cacheToggle = document.getElementById('use-cache');
    if (cacheToggle) {
        cacheToggle.addEventListener('change', function() {
            // Reset the toggle after using it once for a single request
            const useCache = this.checked;
            loadStockData(useCache);
            
            // Reset to default after using
            setTimeout(() => {
                this.checked = true;
            }, 1000);
        });
    }
    
    // Add event listener to clear cache button if it exists
    const clearCacheBtn = document.getElementById('clear-cache');
    if (clearCacheBtn) {
        clearCacheBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to clear cached screening results?')) {
                clearDatabaseCache();
            }
        });
    }
    
    // Load market movers data
    function loadMarketMovers() {
        // Show loading state
        if (marketMoversLoading) marketMoversLoading.classList.remove('d-none');
        if (marketMoversTable) marketMoversTable.classList.add('d-none');
        if (marketMoversError) marketMoversError.classList.add('d-none');
        
        // Fetch market movers data
        fetch('/api/market_movers')
            .then(response => response.json())
            .then(data => {
                // Hide loading state
                if (marketMoversLoading) marketMoversLoading.classList.add('d-none');
                
                // Check for success
                if (!data.success) {
                    throw new Error(data.error || 'Failed to load market movers');
                }
                
                // Check if we have results
                if (!data.market_movers || data.market_movers.length === 0) {
                    throw new Error('No market movers data available');
                }
                
                // Populate the table
                if (marketMoversBody) {
                    marketMoversBody.innerHTML = '';
                    
                    data.market_movers.forEach(stock => {
                        const row = document.createElement('tr');
                        const isPositive = parseFloat(stock.percent_change) > 0;
                        const changeClass = isPositive ? 'text-success' : 'text-danger';
                        const changeIcon = isPositive 
                            ? '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-trending-up"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>'
                            : '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-trending-down"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline><polyline points="17 18 23 18 23 12"></polyline></svg>';
                        
                        row.innerHTML = `
                            <td><strong>${stock.symbol}</strong></td>
                            <td>${stock.name || '-'}</td>
                            <td>$${formatNumber(stock.last_price)}</td>
                            <td class="${changeClass}">
                                ${changeIcon} ${stock.change > 0 ? '+' : ''}${formatNumber(stock.change)}
                            </td>
                            <td class="${changeClass}">
                                ${formatPercent(stock.percent_change, 2)}
                            </td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary view-details-mover" data-symbol="${stock.symbol}">
                                    View
                                </button>
                            </td>
                        `;
                        
                        marketMoversBody.appendChild(row);
                    });
                    
                    // Add event listeners to view buttons
                    document.querySelectorAll('.view-details-mover').forEach(button => {
                        button.addEventListener('click', function() {
                            const symbol = this.getAttribute('data-symbol');
                            showStockDetail(symbol);
                        });
                    });
                    
                    // Show the table
                    if (marketMoversTable) marketMoversTable.classList.remove('d-none');
                }
            })
            .catch(error => {
                console.error('Error loading market movers:', error);
                if (marketMoversLoading) marketMoversLoading.classList.add('d-none');
                if (marketMoversError) {
                    marketMoversError.classList.remove('d-none');
                    marketMoversError.textContent = `Could not load market movers: ${error.message}`;
                }
            });
    }
    
    // Initial loads
    loadStockData(true);
    loadDatabaseStats();
    loadMarketMovers();
});
