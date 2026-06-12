# Binance Futures Testnet Trading Bot

A small Python 3 application for placing `MARKET` and `LIMIT` orders on Binance USDT-M Futures Testnet.

## Features

- Places Binance Futures Testnet orders through direct signed REST calls.
- Supports `BUY` and `SELL`.
- Supports `MARKET` and `LIMIT` order types.
- Validates CLI input before sending an API request.
- Syncs signed request timestamps with Binance server time.
- Separates API, order, validation, CLI, and logging code.
- Logs API requests, responses, and errors to `logs/trading_bot.log`.

## Setup

1. Create and activate a Binance Futures Testnet account.
2. Generate API credentials from the Futures Testnet portal.
3. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

4. Set your credentials. You can either create a local `.env` file:

```text
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
BINANCE_BASE_URL=https://testnet.binancefuture.com
```

or export the variables in your shell.

PowerShell:

```powershell
$env:BINANCE_API_KEY="your_testnet_api_key"
$env:BINANCE_API_SECRET="your_testnet_api_secret"
```

macOS/Linux:

```bash
export BINANCE_API_KEY="your_testnet_api_key"
export BINANCE_API_SECRET="your_testnet_api_secret"
```

The app uses this required testnet URL by default:

```text
https://testnet.binancefuture.com
```

## Run Examples

Market buy:

```bash
python -m trading_bot --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

Market sell:

```bash
python -m trading_bot --symbol BTCUSDT --side SELL --type MARKET --quantity 0.001
```

Limit buy:

```bash
python -m trading_bot --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 50000
```

Limit sell:

```bash
python -m trading_bot --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 120000 --time-in-force GTC
```

## Output

The CLI prints:

- Order request summary
- Order response details, including `orderId`, `status`, `executedQty`, and `avgPrice` when Binance returns them
- Success or failure message

## Logs

Runtime logs are written to:

```text
logs/trading_bot.log
```

This repository also includes sanitized example log files:

- `logs/sample_market_order.log`
- `logs/sample_limit_order.log`

They show the expected request/response logging format without exposing real API credentials or signatures.

## Assumptions

- The Binance Futures Testnet account has enough test USDT balance.
- Quantities and prices must satisfy Binance symbol filters. The bot validates basic input locally, while Binance performs final exchange-rule validation.
- API keys must have Futures Testnet trading permission.
- This application is for testnet/hiring-task use only, not production trading.

## Project Structure

```text
trading_bot/
  __main__.py
  bot/
    __init__.py
    client.py
    env_loader.py
    orders.py
    validators.py
    logging_config.py
    cli.py
requirements.txt
README.md
logs/
  sample_market_order.log
  sample_limit_order.log
```
