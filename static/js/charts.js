/**
 * Create a price chart with moving averages
 * @param {string} canvasId - The ID of the canvas element
 * @param {Object} data - The chart data with dates, prices and moving averages
 */
function createPriceChart(canvasId, data) {
    // Ensure we have the canvas element
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`Canvas element with ID ${canvasId} not found`);
        return;
    }
    
    // Clear any existing chart
    if (canvas.chart) {
        canvas.chart.destroy();
    }
    
    // Create the datasets
    const datasets = [
        {
            label: 'Price',
            data: data.prices,
            borderColor: 'rgba(75, 192, 192, 1)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.1
        }
    ];
    
    // Add moving averages if available
    if (data.sma50 && data.sma50.length) {
        datasets.push({
            label: '50-day SMA',
            data: data.sma50,
            borderColor: 'rgba(255, 159, 64, 1)',
            borderWidth: 1.5,
            pointRadius: 0,
            borderDash: [],
            fill: false
        });
    }
    
    if (data.sma100 && data.sma100.length) {
        datasets.push({
            label: '100-day SMA',
            data: data.sma100,
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1.5,
            pointRadius: 0,
            borderDash: [],
            fill: false
        });
    }
    
    if (data.sma200 && data.sma200.length) {
        datasets.push({
            label: '200-day SMA',
            data: data.sma200,
            borderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 2,
            pointRadius: 0,
            borderDash: [],
            fill: false
        });
    }
    
    // Create the chart
    canvas.chart = new Chart(canvas, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        maxRotation: 0,
                        callback: function(value, index, values) {
                            // Only show a subset of dates for readability
                            if (index === 0 || index === data.dates.length - 1 || index % Math.floor(data.dates.length / 5) === 0) {
                                return data.dates[index];
                            }
                            return '';
                        }
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)'
                    }
                }
            }
        }
    });
}

/**
 * Create a small mini-chart for the stock card
 * @param {string} canvasId - The ID of the canvas element
 * @param {Object} data - The chart data with dates and prices
 */
function createMiniChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`Canvas element with ID ${canvasId} not found`);
        return;
    }
    
    // Clear any existing chart
    if (canvas.chart) {
        canvas.chart.destroy();
    }
    
    // Create a simple chart with just the price line
    canvas.chart = new Chart(canvas, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: 'Price',
                data: data.prices,
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderWidth: 1.5,
                pointRadius: 0,
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    display: false
                }
            },
            elements: {
                line: {
                    tension: 0.4
                }
            }
        }
    });
}
