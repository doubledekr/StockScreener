export const formatNumber = (num: number | undefined, decimals: number = 2): string => {
  if (num === undefined || num === null || isNaN(num)) return 'N/A';
  
  if (Math.abs(num) >= 1e9) {
    return (num / 1e9).toFixed(decimals) + 'B';
  } else if (Math.abs(num) >= 1e6) {
    return (num / 1e6).toFixed(decimals) + 'M';
  } else if (Math.abs(num) >= 1e3) {
    return (num / 1e3).toFixed(decimals) + 'K';
  }
  
  return num.toFixed(decimals);
};

export const formatPercent = (num: number | undefined, decimals: number = 2): string => {
  if (num === undefined || num === null || isNaN(num)) return 'N/A';
  return num.toFixed(decimals) + '%';
};

export const formatCurrency = (num: number | undefined, decimals: number = 2): string => {
  if (num === undefined || num === null || isNaN(num)) return 'N/A';
  return '$' + formatNumber(num, decimals);
};

export const formatVolume = (volume: number | undefined): string => {
  if (volume === undefined || volume === null || isNaN(volume)) return 'N/A';
  return formatNumber(volume, 0);
};

export const getChangeColor = (change: number | undefined): string => {
  if (change === undefined || change === null || isNaN(change)) return '#666';
  return change >= 0 ? '#4CAF50' : '#F44336';
};

export const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  } catch {
    return dateString;
  }
};

export const formatDateTime = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  } catch {
    return dateString;
  }
};