import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { HomeScreen } from './src/screens/HomeScreen';
import { StockDetailScreen } from './src/screens/StockDetailScreen';
import { StockWithScreening } from './src/types';

export type RootStackParamList = {
  Home: undefined;
  StockDetail: { stock: StockWithScreening };
};

const Stack = createStackNavigator<RootStackParamList>();

const App: React.FC = () => {
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="Home"
        screenOptions={{
          headerStyle: {
            backgroundColor: '#007AFF',
          },
          headerTintColor: '#FFFFFF',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        }}
      >
        <Stack.Screen
          name="Home"
          component={HomeScreen}
          options={{
            headerShown: false,
          }}
        />
        <Stack.Screen
          name="StockDetail"
          component={StockDetailScreen}
          options={{
            title: 'Stock Details',
          }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default App;