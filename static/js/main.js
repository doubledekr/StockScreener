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
        
        // Determine if the stock meets all criteria - use a gold border for stocks that meet all criteria
        const cardClass = stock.meets_all_criteria ? 'card h-100 border-warning' : 'card h-100';
        
        card.innerHTML = `
            <div class="${cardClass}">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">
                        ${stock.symbol}
                        ${stock.meets_all_criteria ? '<span class="badge bg-warning text-dark ms-2">All Criteria</span>' : ''}
                    </h5>
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
                    
                    ${stock.price_targets && stock.price_targets.upside !== undefined && stock.price_targets.upside !== null ? 
                    `<div class="row mt-2">
                        <div class="col-6">
                            <div class="small text-muted">Price Target</div>
                            <div>${stock.price_targets.avg ? '$' + formatNumber(stock.price_targets.avg) : 'N/A'}</div>
                        </div>
                        <div class="col-6">
                            <div class="small text-muted">Upside</div>
                            <div class="${stock.price_targets.upside > 0 ? 'text-success' : 'text-danger'}">
                                ${formatPercent(stock.price_targets.upside)}
                            </div>
                        </div>
                    </div>` : ''}
                    
                    ${stock.analyst_ratings && stock.analyst_ratings.analyst_count > 0 ? 
                    `<div class="row mt-2">
                        <div class="col-12">
                            <div class="small text-muted">Analyst Ratings (${stock.analyst_ratings.analyst_count})</div>
                            <div class="d-flex">
                                <span class="badge bg-success me-1">${stock.analyst_ratings.buy_ratings || 0} Buy</span>
                                <span class="badge bg-secondary me-1">${stock.analyst_ratings.hold_ratings || 0} Hold</span>
                                <span class="badge bg-danger">${stock.analyst_ratings.sell_ratings || 0} Sell</span>
                            </div>
                        </div>
                    </div>` : ''}
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
                modalStockName.textContent = stock.company_name || symbol;
                
                // Add a badge if stock meets all criteria
                let symbolText = symbol;
                if (stock.meets_all_criteria) {
                    symbolText += ' <span class="badge bg-warning text-dark">Meets All Criteria</span>';
                }
                modalStockSymbol.innerHTML = symbolText;
                
                // Make sure tech_data and fund_data exist
                const tech_data = stock.technical_data || {};
                const fund_data = stock.fundamental_data || {};
                
                // Safely calculate percentages
                const calcPercent = (a, b) => {
                    if (a === null || a === undefined || b === null || b === undefined || b === 0) {
                        return 'N/A';
                    }
                    return formatPercent(((a / b) - 1) * 100, 1);
                };
                
                // Populate technical metrics with safer data checks
                technicalMetrics.innerHTML = `
                    ${createMetricRow('Current Price', `$${formatNumber(tech_data.current_price)}`)}
                    ${createMetricRow('200-day SMA', `$${formatNumber(tech_data.sma200)}`)}
                    ${createMetricRow('Price > SMA200', 
                        (tech_data.current_price !== null && tech_data.sma200 !== null && tech_data.sma200 > 0) ? 
                        calcPercent(tech_data.current_price, tech_data.sma200) : 'N/A', 
                        tech_data.price_above_sma200)}
                    ${createMetricRow('SMA200 Slope', 
                        tech_data.sma200_slope !== null ? formatNumber(tech_data.sma200_slope, 4) : 'N/A', 
                        tech_data.sma200_slope_positive)}
                    ${createMetricRow('50-day SMA', `$${formatNumber(tech_data.sma50)}`)}
                    ${createMetricRow('SMA50 > SMA200', 
                        (tech_data.sma50 !== null && tech_data.sma200 !== null && tech_data.sma200 > 0) ? 
                        calcPercent(tech_data.sma50, tech_data.sma200) : 'N/A', 
                        tech_data.sma50_above_sma200)}
                    ${createMetricRow('100-day SMA', `$${formatNumber(tech_data.sma100)}`)}
                    ${createMetricRow('SMA100 > SMA200', 
                        (tech_data.sma100 !== null && tech_data.sma200 !== null && tech_data.sma200 > 0) ? 
                        calcPercent(tech_data.sma100, tech_data.sma200) : 'N/A', 
                        tech_data.sma100_above_sma200)}
                `;
                
                // Populate fundamental metrics with safer data checks
                let fundamentalHTML = `
                    ${createMetricRow('Quarterly Sales Growth', 
                        formatPercent(fund_data.quarterly_sales_growth), 
                        fund_data.quarterly_sales_growth_positive)}
                    ${createMetricRow('Quarterly EPS Growth', 
                        formatPercent(fund_data.quarterly_eps_growth), 
                        fund_data.quarterly_eps_growth_positive)}
                    ${createMetricRow('Est. Sales Growth (Year)', 
                        formatPercent(fund_data.estimated_sales_growth), 
                        fund_data.estimated_sales_growth_positive)}
                    ${createMetricRow('Est. EPS Growth (Year)', 
                        formatPercent(fund_data.estimated_eps_growth), 
                        fund_data.estimated_eps_growth_positive)}
                `;
                
                // Add additional growth metrics if available
                if (fund_data.current_quarter_growth !== undefined && fund_data.current_quarter_growth !== null) {
                    fundamentalHTML += createMetricRow('Current Quarter Growth', formatPercent(fund_data.current_quarter_growth));
                }
                
                if (fund_data.next_quarter_growth !== undefined && fund_data.next_quarter_growth !== null) {
                    fundamentalHTML += createMetricRow('Next Quarter Growth', formatPercent(fund_data.next_quarter_growth));
                }
                
                if (fund_data.current_year_growth !== undefined && fund_data.current_year_growth !== null) {
                    fundamentalHTML += createMetricRow('Current Year Growth', formatPercent(fund_data.current_year_growth));
                }
                
                if (fund_data.next_5_years_growth !== undefined && fund_data.next_5_years_growth !== null) {
                    fundamentalHTML += createMetricRow('5-Year Growth (Annual)', formatPercent(fund_data.next_5_years_growth));
                }
                
                // Add price targets if available
                if (data.price_targets) {
                    fundamentalHTML += `<tr><td colspan="2" class="text-primary fw-bold pt-3">Price Targets</td></tr>`;
                    
                    if (data.price_targets.low !== undefined && data.price_targets.low !== null) {
                        fundamentalHTML += createMetricRow('Target Low', `$${formatNumber(data.price_targets.low)}`);
                    }
                    
                    if (data.price_targets.avg !== undefined && data.price_targets.avg !== null) {
                        fundamentalHTML += createMetricRow('Target Average', `$${formatNumber(data.price_targets.avg)}`);
                    }
                    
                    if (data.price_targets.high !== undefined && data.price_targets.high !== null) {
                        fundamentalHTML += createMetricRow('Target High', `$${formatNumber(data.price_targets.high)}`);
                    }
                    
                    if (data.price_targets.upside !== undefined && data.price_targets.upside !== null) {
                        fundamentalHTML += createMetricRow('Upside Potential', 
                            formatPercent(data.price_targets.upside), 
                            data.price_targets.upside > 0);
                    }
                }
                
                // Add analyst ratings if available
                if (data.analyst_ratings) {
                    fundamentalHTML += `<tr><td colspan="2" class="text-primary fw-bold pt-3">Analyst Ratings</td></tr>`;
                    
                    if (data.analyst_ratings.analyst_count !== undefined && data.analyst_ratings.analyst_count !== null && data.analyst_ratings.analyst_count > 0) {
                        fundamentalHTML += createMetricRow('Analysts Covering', data.analyst_ratings.analyst_count);
                        
                        if (data.analyst_ratings.buy_ratings !== undefined && data.analyst_ratings.buy_ratings !== null) {
                            fundamentalHTML += createMetricRow('Buy Ratings', data.analyst_ratings.buy_ratings);
                        }
                        
                        if (data.analyst_ratings.hold_ratings !== undefined && data.analyst_ratings.hold_ratings !== null) {
                            fundamentalHTML += createMetricRow('Hold Ratings', data.analyst_ratings.hold_ratings);
                        }
                        
                        if (data.analyst_ratings.sell_ratings !== undefined && data.analyst_ratings.sell_ratings !== null) {
                            fundamentalHTML += createMetricRow('Sell Ratings', data.analyst_ratings.sell_ratings);
                        }
                        
                        // Add detailed analyst ratings if available
                        if (data.analyst_ratings.detailed_ratings && data.analyst_ratings.detailed_ratings.length > 0) {
                            fundamentalHTML += `
                                <tr>
                                    <td colspan="2" class="pt-2">
                                        <div class="small fw-bold mb-1">Recent Analyst Actions</div>
                                        <div class="table-responsive">
                                            <table class="table table-sm table-striped table-hover">
                                                <thead>
                                                    <tr>
                                                        <th>Date</th>
                                                        <th>Firm</th>
                                                        <th>Action</th>
                                                        <th>Rating</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    ${data.analyst_ratings.detailed_ratings.slice(0, 5).map(rating => `
                                                        <tr>
                                                            <td>${rating.date}</td>
                                                            <td>${rating.firm}</td>
                                                            <td>${rating.rating_change}</td>
                                                            <td>${rating.rating_current}</td>
                                                        </tr>
                                                    `).join('')}
                                                </tbody>
                                            </table>
                                        </div>
                                    </td>
                                </tr>
                            `;
                        }
                    } else {
                        fundamentalHTML += `<tr><td colspan="2" class="text-muted small">No analyst coverage available</td></tr>`;
                    }
                }
                
                // Add a message if no fundamental data is available
                if (Object.keys(fund_data).filter(key => fund_data[key] !== null && fund_data[key] !== undefined).length === 0 &&
                    (!data.price_targets || Object.keys(data.price_targets).length === 0) &&
                    (!data.analyst_ratings || Object.keys(data.analyst_ratings).length === 0)) {
                    fundamentalHTML += `<tr><td colspan="2" class="text-center text-muted">
                        <small>No fundamental data available for this stock.</small>
                    </td></tr>`;
                }
                
                fundamentalMetrics.innerHTML = fundamentalHTML;
                
                // Create the price chart if data available
                if (stock.chart_data && Object.keys(stock.chart_data).length > 0) {
                    try {
                        createPriceChart('priceChart', stock.chart_data);
                    } catch (chartError) {
                        console.error('Error creating chart:', chartError);
                        document.getElementById('chart-container').innerHTML = `
                            <div class="alert alert-warning">
                                <small>Chart data is incomplete or unavailable for this stock.</small>
                            </div>
                        `;
                    }
                } else {
                    document.getElementById('chart-container').innerHTML = `
                        <div class="alert alert-warning">
                            <small>No chart data available for this stock.</small>
                        </div>
                    `;
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
                modalStockSymbol.textContent = symbol;
                technicalMetrics.innerHTML = `<tr><td colspan="2" class="text-center text-danger">
                    <small>Error loading stock details: ${error.message}</small>
                </td></tr>`;
                fundamentalMetrics.innerHTML = `<tr><td colspan="2" class="text-center text-muted">
                    <small>This issue may occur when the stock lacks sufficient trading history or fundamental data.</small>
                </td></tr>`;
                document.getElementById('chart-container').innerHTML = `
                    <div class="alert alert-warning">
                        <small>No chart data available for this stock.</small>
                    </div>
                `;
            });
    }
    
    // Refresh premium data (price targets and analyst ratings)
    document.getElementById('refresh-premium-data')?.addEventListener('click', function() {
        // Show confirmation dialog
        if (!confirm('This will refresh price targets and analyst ratings for 10 popular stocks. Continue?')) {
            return;
        }
        
        // Disable the button and show loading state
        this.disabled = true;
        const originalHtml = this.innerHTML;
        this.innerHTML = `
            <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            <span class="visually-hidden">Loading...</span>
        `;
        
        // Call the API to refresh premium data
        fetch('/api/refresh/premium_data', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            // Re-enable the button
            this.disabled = false;
            this.innerHTML = originalHtml;
            
            if (data.success) {
                // Show success toast
                alert(`Successfully refreshed premium data for ${data.refreshed.length} stocks. Reload the page to see the updated data.`);
                
                // Reload analyst picks
                loadAnalystPicks();
            } else {
                // Show error message
                alert(`Error refreshing premium data: ${data.error}`);
            }
        })
        .catch(error => {
            // Re-enable the button
            this.disabled = false;
            this.innerHTML = originalHtml;
            
            // Show error message
            alert(`Error refreshing premium data: ${error.message}`);
        });
    });
    
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
                            statsHtml += `<div>Stocks passing criteria: ${stats.passing_stocks}</div>`;
                            
                            // Add strict criteria count if available
                            if (stats.strict_passing_stocks !== undefined) {
                                statsHtml += `<div>Stocks meeting ALL criteria: ${stats.strict_passing_stocks}</div>`;
                            }
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
    // Load analyst picks data
    function loadAnalystPicks() {
        const picksLoading = document.getElementById('analyst-picks-loading');
        const picksError = document.getElementById('analyst-picks-error');
        const picksTable = document.getElementById('analyst-picks-table');
        const picksBody = document.getElementById('analyst-picks-body');
        
        if (!picksLoading || !picksError || !picksTable || !picksBody) {
            return;
        }
        
        // Show loading, hide table and error
        picksLoading.classList.remove('d-none');
        picksTable.classList.add('d-none');
        picksError.classList.add('d-none');
        
        // Fetch analyst picks
        fetch('/api/analyst_picks')
            .then(response => response.json())
            .then(data => {
                // Hide loading, show table
                picksLoading.classList.add('d-none');
                picksTable.classList.remove('d-none');
                
                if (!data.success || !data.stocks || data.stocks.length === 0) {
                    throw new Error('No analyst picks data available');
                }
                
                // Clear the table
                picksBody.innerHTML = '';
                
                // Add rows for each analyst pick
                data.stocks.forEach(stock => {
                    const row = document.createElement('tr');
                    
                    // Get price target and upside data
                    const priceTarget = stock.price_targets && stock.price_targets.avg ? `$${formatNumber(stock.price_targets.avg)}` : 'N/A';
                    let upside = 'N/A';
                    let upsideClass = '';
                    
                    if (stock.price_targets && stock.price_targets.upside !== null && stock.price_targets.upside !== undefined) {
                        upside = formatPercent(stock.price_targets.upside);
                        upsideClass = stock.price_targets.upside > 0 ? 'text-success' : 'text-danger';
                    }
                    
                    // Create analyst ratings display
                    let analystRatings = 'N/A';
                    if (stock.analyst_ratings && stock.analyst_ratings.analyst_count > 0) {
                        analystRatings = `
                            <div class="d-flex mb-2">
                                <span class="badge bg-success me-1">${stock.analyst_ratings.buy_ratings || 0} Buy</span>
                                <span class="badge bg-secondary me-1">${stock.analyst_ratings.hold_ratings || 0} Hold</span>
                                <span class="badge bg-danger">${stock.analyst_ratings.sell_ratings || 0} Sell</span>
                            </div>
                        `;
                        
                        // Add most recent analyst action if available
                        if (stock.analyst_ratings.detailed_ratings && stock.analyst_ratings.detailed_ratings.length > 0) {
                            const mostRecent = stock.analyst_ratings.detailed_ratings[0];
                            analystRatings += `
                                <div class="small text-muted mt-1">
                                    Latest: ${mostRecent.firm} - ${mostRecent.rating_change} ${mostRecent.rating_current}
                                </div>
                            `;
                        }
                    }
                    
                    row.innerHTML = `
                        <td>${stock.symbol}</td>
                        <td class="text-truncate" style="max-width: 150px;">${stock.company_name || 'Unknown'}</td>
                        <td>${analystRatings}</td>
                        <td>${priceTarget}</td>
                        <td>$${formatNumber(stock.technical_data.current_price)}</td>
                        <td class="${upsideClass}">${upside}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary view-details" data-symbol="${stock.symbol}">
                                Details
                            </button>
                        </td>
                    `;
                    
                    picksBody.appendChild(row);
                });
            })
            .catch(error => {
                console.error('Error loading analyst picks:', error);
                picksLoading.classList.add('d-none');
                picksError.classList.remove('d-none');
                picksError.textContent = `Could not load analyst picks. ${error.message}`;
            });
    }
    
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
    loadAnalystPicks();
});
