import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  FlatList,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { StockCard } from '../components/StockCard';
import { MarketMoverCard } from '../components/MarketMoverCard';
import { useStocks } from '../hooks/useStocks';
import { StockWithScreening, MarketMover } from '../types';

interface HomeScreenProps {
  navigation: any;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({ navigation }) => {
  const {
    stocks,
    marketMovers,
    loading,
    error,
    refreshing,
    refreshData,
    getStockDetails,
  } = useStocks();

  const [activeTab, setActiveTab] = useState<'screened' | 'movers'>('screened');

  const handleStockPress = async (symbol: string) => {
    try {
      const stockDetails = await getStockDetails(symbol);
      if (stockDetails) {
        navigation.navigate('StockDetail', { stock: stockDetails });
      }
    } catch (err) {
      Alert.alert('Error', 'Failed to load stock details');
    }
  };

  const renderStockCard = ({ item }: { item: StockWithScreening }) => (
    <StockCard stock={item} onPress={handleStockPress} />
  );

  const renderMarketMover = ({ item }: { item: MarketMover }) => (
    <MarketMoverCard mover={item} onPress={handleStockPress} />
  );

  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={refreshData}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Stock Screener</Text>
        
        <View style={styles.tabContainer}>
          <TouchableOpacity
            style={[
              styles.tab,
              activeTab === 'screened' && styles.activeTab,
            ]}
            onPress={() => setActiveTab('screened')}
          >
            <Text
              style={[
                styles.tabText,
                activeTab === 'screened' && styles.activeTabText,
              ]}
            >
              Screened Stocks ({stocks.length})
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[
              styles.tab,
              activeTab === 'movers' && styles.activeTab,
            ]}
            onPress={() => setActiveTab('movers')}
          >
            <Text
              style={[
                styles.tabText,
                activeTab === 'movers' && styles.activeTabText,
              ]}
            >
              Market Movers ({marketMovers.length})
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {activeTab === 'screened' ? (
        <FlatList
          data={stocks}
          renderItem={renderStockCard}
          keyExtractor={(item) => item.symbol}
          contentContainerStyle={styles.listContainer}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={refreshData} />
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyText}>
                {loading ? 'Loading screened stocks...' : 'No stocks found matching criteria'}
              </Text>
            </View>
          }
        />
      ) : (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.moversContainer}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={refreshData} />
          }
        >
          {marketMovers.map((mover) => (
            <MarketMoverCard
              key={mover.symbol}
              mover={mover}
              onPress={handleStockPress}
            />
          ))}
          {marketMovers.length === 0 && !loading && (
            <View style={styles.emptyContainer}>
              <Text style={styles.emptyText}>No market movers available</Text>
            </View>
          )}
        </ScrollView>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    backgroundColor: '#FFFFFF',
    paddingTop: 60,
    paddingBottom: 16,
    paddingHorizontal: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1A1A1A',
    marginBottom: 16,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#F0F0F0',
    borderRadius: 8,
    padding: 4,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignItems: 'center',
  },
  activeTab: {
    backgroundColor: '#007AFF',
  },
  tabText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666666',
  },
  activeTabText: {
    color: '#FFFFFF',
  },
  listContainer: {
    paddingVertical: 8,
  },
  moversContainer: {
    paddingVertical: 16,
    paddingHorizontal: 8,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 16,
    color: '#666666',
    textAlign: 'center',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  errorText: {
    fontSize: 16,
    color: '#F44336',
    textAlign: 'center',
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});