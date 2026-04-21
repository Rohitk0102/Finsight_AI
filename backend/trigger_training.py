from app.tasks.model_training import train_xgboost, train_prophet, train_lstm_task

tickers = ['AAPL', 'RELIANCE.NS', 'TCS.NS']
for t in tickers:
    train_xgboost.delay(t)
    train_prophet.delay(t)
    train_lstm_task.delay(t)
    print(f'Dispatched: {t}')

print('Done — watch Terminal 2 for progress')
