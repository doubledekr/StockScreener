# Stock Screener React Native App

A React Native TypeScript application that provides advanced stock screening capabilities with real-time market data integration through the TwelveData API.

## Features

- **Real-time Stock Screening**: Advanced filtering based on technical and fundamental criteria
- **Market Movers**: Track stocks with significant price movements
- **Interactive Charts**: Visual price data with moving averages
- **Detailed Stock Analysis**: Comprehensive fundamental and technical metrics
- **TypeScript Support**: Full type safety and enhanced development experience
- **Responsive Design**: Optimized for mobile devices

## Technical Stack

- **React Native**: Cross-platform mobile development
- **TypeScript**: Type-safe JavaScript development
- **React Navigation**: Navigation library for screen management
- **TwelveData API**: Real-time financial market data
- **React Native Chart Kit**: Interactive financial charts
- **AsyncStorage**: Local data caching and persistence

## Project Structure

```
├── src/
│   ├── types/            # TypeScript interface definitions
│   ├── services/         # API service layer
│   ├── components/       # Reusable UI components
│   ├── screens/          # Application screens
│   ├── hooks/            # Custom React hooks
│   └── utils/            # Utility functions
├── App.tsx               # Main application component
├── index.js              # React Native entry point
└── tsconfig.json         # TypeScript configuration
```

## Key Components

### API Service (`src/services/api.ts`)
- Handles all TwelveData API interactions
- Implements caching strategies for performance
- Provides type-safe data transformation
- Manages rate limiting and error handling

### Stock Components
- **StockCard**: Displays screening results with key metrics
- **MarketMoverCard**: Shows stocks with significant price movements
- **StockDetailScreen**: Comprehensive stock analysis view

### Data Management
- **useStocks Hook**: Centralized state management for stock data
- **Type Definitions**: Complete TypeScript interfaces for all data structures
- **Formatters**: Consistent number and currency formatting

## Screening Criteria

The application implements sophisticated stock screening based on:

### Technical Analysis
- Price above 200-day Simple Moving Average
- 50-day SMA above 200-day SMA
- 100-day SMA above 200-day SMA
- Positive SMA slope trends

### Fundamental Analysis
- Quarterly revenue growth
- Quarterly EPS growth
- Estimated sales growth
- Estimated EPS growth
- P/E ratio analysis
- Market capitalization metrics

## Setup Instructions

### Prerequisites
- Node.js 16+ 
- React Native CLI
- Android Studio (for Android development)
- Xcode (for iOS development)

### Installation

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **iOS Setup** (iOS only)
   ```bash
   cd ios && pod install && cd ..
   ```

3. **Start Metro Bundler**
   ```bash
   npm start
   ```

4. **Run the Application**
   
   For Android:
   ```bash
   npm run android
   ```
   
   For iOS:
   ```bash
   npm run ios
   ```

## API Configuration

The application uses the TwelveData API for financial data. The API key is configured in the environment variables and integrated into the service layer.

### API Endpoints Used
- Market movers data
- Stock quotes and time series
- Company profiles and fundamentals
- Analyst ratings and price targets
- Growth estimates and earnings data

## Data Flow

1. **Market Data Retrieval**: Fetch real-time market movers and stock universe
2. **Technical Screening**: Apply moving average and trend analysis
3. **Fundamental Analysis**: Evaluate financial metrics and growth indicators
4. **Scoring System**: Calculate composite scores for stock ranking
5. **Caching Strategy**: Store processed data for improved performance

## Performance Optimizations

- **Batch API Requests**: Process multiple stocks simultaneously
- **Local Caching**: Reduce API calls with AsyncStorage
- **Lazy Loading**: Load detailed data on demand
- **Efficient Rendering**: Optimized FlatList for large datasets

## Future Enhancements

- Push notifications for screening alerts
- Portfolio tracking capabilities
- Additional chart types and technical indicators
- Customizable screening criteria
- Offline data synchronization

## Development

### TypeScript Configuration
The project uses strict TypeScript settings for enhanced code quality and type safety.

### Code Organization
- Modular component architecture
- Separation of concerns between UI and business logic
- Centralized API management
- Consistent naming conventions

This React Native TypeScript application provides a comprehensive stock screening solution with professional-grade features and robust architecture for financial market analysis.