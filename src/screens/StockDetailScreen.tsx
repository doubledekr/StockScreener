import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { StockWithScreening, ChartData } from '../types';
import { formatCurrency, formatPercent, formatNumber, getChangeColor } from '../utils/formatters';
import ApiService from '../services/api';

interface StockDetailScreenProps {
  route: {
    params: {
      stock: StockWithScreening;
    };
  };
  navigation: any;
}

const { width } = Dimensions.get('window');

export const StockDetailScreen: React.FC<StockDetailScreenProps> = ({ route, navigation }) => {
  const { stock } = route.params;
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    navigation.setOptions({
      title: stock.symbol,
    });
    loadChartData();
  }, [stock.symbol, navigation]);

  const loadChartData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await ApiService.getChartData(stock.symbol);
      
      if (response.success && response.data) {
        setChartData(response.data);
      } else {
        setError(response.error || 'Failed to load chart data');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load chart data');
    } finally {
      setLoading(false);
    }
  };

  const changeColor = getChangeColor(stock.price_change_percent);

  const renderMetricRow = (label: string, value: string | number | undefined, isPositive?: boolean | null) => (
    <View style={styles.metricRow}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={[
        styles.metricValue,
        isPositive !== null && {
          color: isPositive ? '#4CAF50' : '#F44336'
        }
      ]}>
        {value || 'N/A'}
      </Text>
    </View>
  );

  const renderChart = () => {
    if (loading) {
      return (
        <View style={styles.chartContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading chart...</Text>
        </View>
      );
    }

    if (error || !chartData) {
      return (
        <View style={styles.chartContainer}>
          <Text style={styles.errorText}>{error || 'Chart data unavailable'}</Text>
        </View>
      );
    }

    const chartConfig = {
      backgroundColor: '#FFFFFF',
      backgroundGradientFrom: '#FFFFFF',
      backgroundGradientTo: '#FFFFFF',
      decimalPlaces: 2,
      color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
      labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
      style: {
        borderRadius: 16,
      },
      propsForDots: {
        r: '0',
      },
    };

    return (
      <View style={styles.chartContainer}>
        <Text style={styles.chartTitle}>Price Chart (6 Months)</Text>
        <LineChart
          data={{
            labels: chartData.dates.filter((_, index) => index % 30 === 0).slice(-6),
            datasets: [
              {
                data: chartData.prices.slice(-180),
                color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
                strokeWidth: 2,
              },
            ],
          }}
          width={width - 32}
          height={220}
          chartConfig={chartConfig}
          bezier
          style={styles.chart}
        />
      </View>
    );
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.titleContainer}>
          <Text style={styles.symbol}>{stock.symbol}</Text>
          <Text style={styles.companyName}>{stock.company_name || 'N/A'}</Text>
        </View>
        <View style={styles.priceContainer}>
          <Text style={styles.price}>{formatCurrency(stock.current_price)}</Text>
          <Text style={[styles.change, { color: changeColor }]}>
            {formatPercent(stock.price_change_percent)}
          </Text>
        </View>
      </View>

      {renderChart()}

      {stock.screening_result && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Screening Results</Text>
          <View style={styles.card}>
            <View style={styles.scoreContainer}>
              <Text style={styles.scoreLabel}>Score</Text>
              <Text style={styles.scoreValue}>
                {stock.screening_result.score?.toFixed(1) || 'N/A'}
              </Text>
            </View>
            
            <View style={styles.criteriaGrid}>
              <View style={styles.criteriaItem}>
                <View style={[
                  styles.criteriaIndicator,
                  { backgroundColor: stock.screening_result.price_above_sma200 ? '#4CAF50' : '#F44336' }
                ]} />
                <Text style={styles.criteriaText}>Price above SMA200</Text>
              </View>
              <View style={styles.criteriaItem}>
                <View style={[
                  styles.criteriaIndicator,
                  { backgroundColor: stock.screening_result.sma50_above_sma200 ? '#4CAF50' : '#F44336' }
                ]} />
                <Text style={styles.criteriaText}>SMA50 above SMA200</Text>
              </View>
              <View style={styles.criteriaItem}>
                <View style={[
                  styles.criteriaIndicator,
                  { backgroundColor: stock.screening_result.sma100_above_sma200 ? '#4CAF50' : '#F44336' }
                ]} />
                <Text style={styles.criteriaText}>SMA100 above SMA200</Text>
              </View>
            </View>

            {renderMetricRow('Current Price', formatCurrency(stock.screening_result.current_price))}
            {renderMetricRow('SMA 50', formatCurrency(stock.screening_result.sma50))}
            {renderMetricRow('SMA 100', formatCurrency(stock.screening_result.sma100))}
            {renderMetricRow('SMA 200', formatCurrency(stock.screening_result.sma200))}
          </View>
        </View>
      )}

      {stock.fundamentals && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Fundamentals</Text>
          <View style={styles.card}>
            {renderMetricRow('Market Cap', formatCurrency(stock.fundamentals.market_cap))}
            {renderMetricRow('P/E Ratio', stock.fundamentals.pe_ratio?.toFixed(2))}
            {renderMetricRow('EPS', formatCurrency(stock.fundamentals.eps))}
            {renderMetricRow('Beta', stock.fundamentals.beta?.toFixed(2))}
            {renderMetricRow('Dividend Yield', formatPercent(stock.fundamentals.dividend_yield))}
            {renderMetricRow('ROE', formatPercent(stock.fundamentals.roe))}
            {renderMetricRow('ROA', formatPercent(stock.fundamentals.roa))}
            {renderMetricRow(
              'Quarterly Revenue Growth',
              formatPercent(stock.fundamentals.quarterly_revenue_growth),
              stock.fundamentals.quarterly_revenue_growth ? stock.fundamentals.quarterly_revenue_growth > 0 : null
            )}
            {renderMetricRow(
              'Quarterly EPS Growth',
              formatPercent(stock.fundamentals.quarterly_eps_growth),
              stock.fundamentals.quarterly_eps_growth ? stock.fundamentals.quarterly_eps_growth > 0 : null
            )}
          </View>
        </View>
      )}

      {stock.fundamentals && (stock.fundamentals.price_target_avg || stock.fundamentals.analyst_count) && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Analyst Information</Text>
          <View style={styles.card}>
            {renderMetricRow('Price Target (Avg)', formatCurrency(stock.fundamentals.price_target_avg))}
            {renderMetricRow('Price Target (Low)', formatCurrency(stock.fundamentals.price_target_low))}
            {renderMetricRow('Price Target (High)', formatCurrency(stock.fundamentals.price_target_high))}
            {renderMetricRow('Target Upside', formatPercent(stock.fundamentals.price_target_upside))}
            {renderMetricRow('Analyst Count', stock.fundamentals.analyst_count)}
            {renderMetricRow('Buy Ratings', stock.fundamentals.buy_ratings)}
            {renderMetricRow('Hold Ratings', stock.fundamentals.hold_ratings)}
            {renderMetricRow('Sell Ratings', stock.fundamentals.sell_ratings)}
          </View>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  titleContainer: {
    flex: 1,
  },
  symbol: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginBottom: 4,
  },
  companyName: {
    fontSize: 16,
    color: '#666666',
  },
  priceContainer: {
    alignItems: 'flex-end',
  },
  price: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginBottom: 4,
  },
  change: {
    fontSize: 16,
    fontWeight: '600',
  },
  chartContainer: {
    backgroundColor: '#FFFFFF',
    margin: 16,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginBottom: 16,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#666666',
  },
  errorText: {
    fontSize: 14,
    color: '#F44336',
    textAlign: 'center',
  },
  section: {
    margin: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginBottom: 12,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  scoreContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  scoreLabel: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1A1A1A',
  },
  scoreValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  criteriaGrid: {
    marginBottom: 16,
  },
  criteriaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  criteriaIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  criteriaText: {
    fontSize: 14,
    color: '#1A1A1A',
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F8F8F8',
  },
  metricLabel: {
    fontSize: 14,
    color: '#666666',
    flex: 1,
  },
  metricValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1A1A1A',
    textAlign: 'right',
  },
});