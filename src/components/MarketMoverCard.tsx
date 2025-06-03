import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { MarketMover } from '../types';
import { formatCurrency, formatPercent, formatVolume, getChangeColor } from '../utils/formatters';

interface MarketMoverCardProps {
  mover: MarketMover;
  onPress: (symbol: string) => void;
}

export const MarketMoverCard: React.FC<MarketMoverCardProps> = ({ mover, onPress }) => {
  const changeColor = getChangeColor(mover.change_percent);
  
  return (
    <TouchableOpacity
      style={styles.container}
      onPress={() => onPress(mover.symbol)}
      activeOpacity={0.7}
    >
      <View style={styles.header}>
        <Text style={styles.symbol}>{mover.symbol}</Text>
        <Text style={styles.price}>{formatCurrency(mover.price)}</Text>
      </View>
      
      <Text style={styles.name} numberOfLines={1}>
        {mover.name}
      </Text>
      
      <View style={styles.footer}>
        <Text style={[styles.change, { color: changeColor }]}>
          {formatPercent(mover.change_percent)}
        </Text>
        <Text style={styles.volume}>
          Vol: {formatVolume(mover.volume)}
        </Text>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 12,
    marginHorizontal: 8,
    marginVertical: 4,
    width: 160,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  symbol: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1A1A1A',
  },
  price: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1A1A1A',
  },
  name: {
    fontSize: 12,
    color: '#666666',
    marginBottom: 8,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  change: {
    fontSize: 14,
    fontWeight: '600',
  },
  volume: {
    fontSize: 10,
    color: '#666666',
  },
});