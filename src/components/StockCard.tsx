import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { StockWithScreening } from '../types';
import { formatCurrency, formatPercent, getChangeColor } from '../utils/formatters';

interface StockCardProps {
  stock: StockWithScreening;
  onPress: (symbol: string) => void;
}

const { width } = Dimensions.get('window');

export const StockCard: React.FC<StockCardProps> = ({ stock, onPress }) => {
  const changeColor = getChangeColor(stock.price_change_percent);
  
  return (
    <TouchableOpacity
      style={styles.container}
      onPress={() => onPress(stock.symbol)}
      activeOpacity={0.7}
    >
      <View style={styles.header}>
        <View style={styles.symbolContainer}>
          <Text style={styles.symbol}>{stock.symbol}</Text>
          <Text style={styles.companyName} numberOfLines={1}>
            {stock.company_name || 'N/A'}
          </Text>
        </View>
        <View style={styles.priceContainer}>
          <Text style={styles.price}>
            {formatCurrency(stock.current_price)}
          </Text>
          <Text style={[styles.change, { color: changeColor }]}>
            {formatPercent(stock.price_change_percent)}
          </Text>
        </View>
      </View>

      {stock.screening_result && (
        <View style={styles.screeningInfo}>
          <View style={styles.criteriaContainer}>
            <Text style={styles.criteriaLabel}>Score:</Text>
            <Text style={styles.criteriaValue}>
              {stock.screening_result.score?.toFixed(1) || 'N/A'}
            </Text>
          </View>
          
          <View style={styles.indicatorsContainer}>
            <View style={[
              styles.indicator,
              { backgroundColor: stock.screening_result.price_above_sma200 ? '#4CAF50' : '#F44336' }
            ]} />
            <View style={[
              styles.indicator,
              { backgroundColor: stock.screening_result.sma50_above_sma200 ? '#4CAF50' : '#F44336' }
            ]} />
            <View style={[
              styles.indicator,
              { backgroundColor: stock.screening_result.sma100_above_sma200 ? '#4CAF50' : '#F44336' }
            ]} />
          </View>
        </View>
      )}

      <View style={styles.fundamentalsContainer}>
        <View style={styles.fundamental}>
          <Text style={styles.fundamentalLabel}>P/E</Text>
          <Text style={styles.fundamentalValue}>
            {stock.fundamentals?.pe_ratio?.toFixed(2) || 'N/A'}
          </Text>
        </View>
        <View style={styles.fundamental}>
          <Text style={styles.fundamentalLabel}>Market Cap</Text>
          <Text style={styles.fundamentalValue}>
            {formatCurrency(stock.fundamentals?.market_cap)}
          </Text>
        </View>
        <View style={styles.fundamental}>
          <Text style={styles.fundamentalLabel}>Beta</Text>
          <Text style={styles.fundamentalValue}>
            {stock.fundamentals?.beta?.toFixed(2) || 'N/A'}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  symbolContainer: {
    flex: 1,
  },
  symbol: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginBottom: 4,
  },
  companyName: {
    fontSize: 14,
    color: '#666666',
    maxWidth: width * 0.5,
  },
  priceContainer: {
    alignItems: 'flex-end',
  },
  price: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginBottom: 4,
  },
  change: {
    fontSize: 14,
    fontWeight: '600',
  },
  screeningInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#F0F0F0',
  },
  criteriaContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  criteriaLabel: {
    fontSize: 14,
    color: '#666666',
    marginRight: 8,
  },
  criteriaValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1A1A1A',
  },
  indicatorsContainer: {
    flexDirection: 'row',
    gap: 6,
  },
  indicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  fundamentalsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  fundamental: {
    alignItems: 'center',
    flex: 1,
  },
  fundamentalLabel: {
    fontSize: 12,
    color: '#666666',
    marginBottom: 4,
  },
  fundamentalValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1A1A1A',
  },
});