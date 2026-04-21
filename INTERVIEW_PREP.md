# 🎤 Finsight AI - Interview Preparation Guide

*Use this guide to confidently explain your project during technical interviews.*

---

## 1. The Elevator Pitch (Start with this)
"Finsight AI is a full-stack, AI-powered stock market prediction and portfolio management platform. It allows users to track their holdings across multiple brokers while providing AI-driven price forecasting, technical screening, and real-time news sentiment analysis."

## 2. The Problem it Solves
"Most retail investors have fragmented portfolios across different brokers (like Zerodha, Upstox, or Groww) and have to jump between different apps for news, technical indicators, and portfolio tracking. Finsight AI solves this by aggregating all portfolio data into a single, beautiful dashboard while supercharging the user's decision-making with Machine Learning price predictions and sentiment analysis."

---

## 3. System Architecture & Tech Stack (The "What" and "Why")

*When the interviewer asks about your tech stack, break it down by layers and confidently explain **why** you chose them over the alternatives:*

### **Frontend: Next.js, React, Tailwind CSS, Clerk (Auth)**
* **What it is:** A fully responsive, highly optimized Server-Side Rendered (SSR) web application with dynamic dark/light themes. 
* **Why Next.js over pure React (Vite/CRA)?** Next.js provides built-in SEO optimization, faster page loads via Server Components, and seamless API routing.
* **Why Clerk?** Building secure authentication from scratch (handling JWTs, password resets, social logins) is reinventing the wheel and highly prone to security vulnerabilities. Clerk provides enterprise-grade authentication out-of-the-box, allowing focus on core business logic.

### **Backend: Python, FastAPI**
* **What it is:** The central nervous system of the app processing HTTP requests, connecting to the database, and routing data to the ML models.
* **Why FastAPI over Django or Flask?** FastAPI is natively asynchronous, meaning it handles high-throughput I/O operations (like fetching stock prices) significantly faster. Furthermore, it automatically generates Swagger/OpenAPI documentation via Pydantic model type-hinting, ensuring the frontend always knows the exact shape of the data.

### **Database: Supabase (PostgreSQL)**
* **What it is:** A relational database used to store users, portfolio holdings, model accuracies, and historical prediction data.
* **Why PostgreSQL over MongoDB?** Financial data is inherently relational (User -> Portfolio -> Asset -> Transaction). A NoSQL database like MongoDB lacks the strict ACID compliance and schema rigidity required to prevent financial data corruption. Supabase was chosen as a robust, managed wrapper around Postgres.

### **Asynchronous Job Queue: Celery + Redis**
* **What it is:** A background task processor. Redis acts as the message broker holding the queue of tasks in memory, while Celery Workers execute them. 
* **Why is this necessary?** Training an ML model or fetching historical data for 28 stock tickers takes minutes. If this ran on the main FastAPI thread, the server would block and users would get "Timeout" errors. Celery executes heavy ML retraining and daily price syncing completely in the background via `Celery Beat` scheduling (e.g., nightly syncs at market close).

### **Machine Learning Pipeline: LSTM, XGBoost, Prophet, FinBERT**
* **What it is:** The predictive engine of the app. It currently tracks and predicts prices for 28 different ticker symbols.
* **Why use an Ensemble approach?** No single model is perfect for financial time series data:
   * **LSTM (Deep Learning):** Great at catching long-term sequential dependencies.
   * **XGBoost:** Excellent at finding non-linear relationships in tabular data extremely quickly.
   * **Prophet:** Built by Meta, highly resilient to missing data and great for spotting holidays/seasonality.
   * By combining them, Finsight AI achieves a Mean Absolute Percentage Error (MAPE) of under 5% on average (e.g., AAPL at 1.9%, Reliance at 2.4%). 
   * **FinBERT:** A pre-trained NLP model specifically fine-tuned on financial text. It accurately classifies news headlines as positive, neutral, or negative.

---

## 4. Technical Challenges to Highlight

*Interviewers love hearing about problems you faced and how you overcame them. Pick one of these based on the role:*

* **Challenge 1: Blocking the Main Thread (Backend Focus)**
  * *"Initially, when a user requested an AI prediction, the backend would try to infer the model on the fly, locking up the server. I solved this by implementing Celery and Redis to offload model training and heavy predictions to background workers, making the main API lightning-fast."*
* **Challenge 2: Hydration Errors & Theming (Frontend Focus)**
  * *"Implementing a dark/light mode in Server-Rendered Next.js caused 'Hydration Mismatch' errors because the server didn't know the user's local theme preference on the first paint. I fixed this by implementing a mounted state listener and using `localStorage` to persist themes safely without flashing the wrong colors on load."*
* **Challenge 3: High Error Rates in ML (Data Science Focus)**
  * *"Stock prices are notoriously noisy and volatile. Early prototypes using simple linear regressions failed entirely. I solved this by transitioning to an ensemble architecture—combining LSTM for sequence memory and XGBoost for catching short-term volatility—bringing the system's average error rate down to under 5%."*

---

## 5. Summary of Impact (The Closing Hook)
"Ultimately, I built a production-ready financial application capable of running locally or via Docker Compose. It routinely runs background cron jobs without supervision, successfully tracks multiple broker accounts securely, and serves highly accurate AI predictions with less than 5% deviation on real asset prices."

---

> **💡 Extra Tip:** If they ask you what you would improve if you had more time, tell them: *"I would implement WebSockets for true real-time price streaming (instead of HTTP polling), and integrate a Circuit Breaker pattern to protect the app if third-party stock APIs experience downtime."*
