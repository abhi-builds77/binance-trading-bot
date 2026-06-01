# Binance Futures Testnet – Trading Bot

A Python CLI application for placing orders on Binance Futures Testnet (USDT-M).  
Supports Market, Limit, and Stop-Limit orders with structured logging and full error handling.

---

## Features

- **Market** and **Limit** orders (BUY / SELL)
- **Bonus:** Stop-Limit orders (`STOP` type)
- **Interactive mode** (`-i`) – guided prompts with inline validation
- Structured logging: DEBUG-level detail to file, INFO to console
- Full error handling: validation errors, API errors, network failures
- Clean layered architecture: `client → orders → validators → cli`

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance Futures HTTP client (signing, requests, errors)
│   ├── orders.py          # Order-type business logic
│   ├── validators.py      # Input validation and coercion
│   └── logging_config.py  # Rotating file + console logging setup
├── logs/
│   ├── market_order_sample.log
│   └── limit_order_sample.log
├── cli.py                 # CLI entry point (argparse + interactive mode)
├── .env.example
├── README.md
└── requirements.txt
```

---

## Setup

### 1. Get Testnet Credentials

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in with your GitHub account
3. Navigate to **API Key** in the top-right user menu
4. Click **Generate** to create a key pair
5. Copy the **API Key** and **Secret Key**

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Credentials

```bash
cp .env.example .env
```

Edit `.env`:

```
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```

---

## How to Run

### Market Order – BUY

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Market Order – SELL

```bash
python cli.py --symbol ETHUSDT --side SELL --type MARKET --quantity 0.01
```

### Limit Order – SELL

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 50000
```

### Limit Order – BUY

```bash
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 40000
```

### Stop-Limit Order (Bonus) – BUY

```bash
python cli.py --symbol BTCUSDT --side BUY --type STOP --quantity 0.001 --price 45000 --stop-price 44500
```

> `--stop-price` is the **trigger** price; `--price` is the limit price placed once triggered.

### Interactive / Guided Mode

```bash
python cli.py --interactive
# or
python cli.py -i
```

Prompts you step-by-step with menus and re-prompts on invalid input.

### Help

```bash
python cli.py --help
```

## Log Files

Logs are written to `logs/trading_bot.log` automatically on first run.

| Level   | Destination    | Content                                      |
|---------|----------------|----------------------------------------------|
| DEBUG   | File only      | Full request params (no signature), responses |
| INFO    | File + console | Order lifecycle, success/failure              |
| ERROR   | File + console | Validation errors, API errors, network errors |

Sample log files are included in `logs/` for reference.

---

## Assumptions

- All orders are placed on **USDT-M Futures Testnet** only (`https://testnet.binancefuture.com`).
- Default `timeInForce` for LIMIT and STOP orders is **GTC** (Good Till Cancelled).
- Credentials are loaded from a `.env` file via `python-dotenv`.
- For STOP orders, `--price` is the limit order price and `--stop-price` is the trigger.
- Quantity and price precision are passed as-is; if Binance rejects with a precision error, adjust to the symbol's tick/step size (viewable on the testnet exchange info endpoint).
- Clock drift tolerance is set to 5 000 ms via `recvWindow`.
