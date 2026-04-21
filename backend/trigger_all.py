from app.tasks.model_training import retrain_all
from app.tasks.sentiment_pipeline import compute_sentiment_all

retrain_all.delay()
print('All 28 tickers queued for retraining')

compute_sentiment_all.delay()
print('Sentiment pipeline queued for all tickers')
