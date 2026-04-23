import React, { useEffect, useState } from 'react';
import { formatPercent } from './utils';
import { finsightApi } from '../../lib/api/client';

interface TickerData {
  symbol: string;
  price: number;
  change: number;
}

const DEFAULT_SYMBOLS = ['AAPL', 'NVDA', 'MSFT', 'TSLA', 'BTC-USD', '^NSEI', 'RELIANCE.NS'];

export function MarketTicker() {
  const [tickers, setTickers] = useState<TickerData[]>([]);

  useEffect(() => {
    let isMounted = true;

    const fetchTickers = async () => {
      try {
        const promises = DEFAULT_SYMBOLS.map(async (symbol) => {
          try {
            const res = await finsightApi.ticker(symbol);
            if (res.status === 200) {
              const data = res.data;
              return {
                symbol: symbol === '^NSEI' ? 'NIFTY' : symbol.replace('.NS', ''),
                price: data.price || 0,
                change: data.change_pct || 0
              };
            }
          } catch (e) {
            console.error(`Failed to fetch ${symbol}`, e);
          }
          return null;
        });

        const results = await Promise.all(promises);
        if (isMounted) {
          const validResults = results.filter((r): r is TickerData => r !== null);
          if (validResults.length > 0) {
            setTickers(validResults);
          }
        }
      } catch (error) {
        console.error("Error fetching market ticker data:", error);
      }
    };

    fetchTickers();
    // Refresh every 60 seconds
    const interval = setInterval(fetchTickers, 60000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  if (tickers.length === 0) {
    return (
      <div className="flex items-center w-full h-8 overflow-hidden text-xs border-b finsight-sidebar-bg finsight-border finsight-theme">
        <div className="px-4 finsight-muted text-[10px] uppercase tracking-widest">
          LOADING MARKET DATA...
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center w-full h-8 overflow-hidden text-xs border-b finsight-sidebar-bg finsight-border finsight-theme">
      <div className="flex animate-shimmer whitespace-nowrap" style={{ animationDuration: '40s', animationTimingFunction: 'linear' }}>
        {[...tickers, ...tickers, ...tickers].map((ticker, i) => (
          <div key={i} className="flex items-center mx-6 gap-2">
            <span className="font-bold text-white">{ticker.symbol}</span>
            <span className="text-[var(--text)]">{ticker.price.toFixed(2)}</span>
            <span className={ticker.change >= 0 ? 'text-[#00d68f]' : 'text-[#ff4d4d]'}>
              {formatPercent(ticker.change)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
