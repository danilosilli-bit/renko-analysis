# Milestone 1 — Step 1: MT5/BRA50 read-only diagnostic

This package contains the first change for `renko-analysis`.

## Goal

Validate the real connection chain:

ActivTrades -> MT5 terminal -> MetaTrader5 Python package -> project code

No order execution is implemented.

## Files

- `ingestion/mt5_client.py`
  - replaces/evolves the existing client;
  - adds connection guards;
  - reads terminal/account information;
  - ensures the requested symbol is selected;
  - reads current ticks;
  - reads symbol contract metadata;
  - reads open positions (read-only);
  - preserves the existing historical tick methods.

- `scripts/diagnose_mt5_bra50.py`
  - diagnostic utility;
  - prints safe terminal/account fields;
  - prints the full subset of BRA50 contract parameters that matter;
  - optionally watches live ticks.

## Installation

From the repository virtual environment:

```powershell
python -m pip install MetaTrader5
```

Do not add FastAPI yet. First validate MT5 reliably.

## Run

1. Open the ActivTrades MT5 terminal.
2. Log into the account.
3. Make sure the symbol is available in Market Watch.
4. From the repository root:

```powershell
python scripts/diagnose_mt5_bra50.py
```

To watch ticks for 30 seconds:

```powershell
python scripts/diagnose_mt5_bra50.py --watch 30
```

If the exact symbol name is not `BRA50`, use the name shown in MT5:

```powershell
python scripts/diagnose_mt5_bra50.py --symbol "EXACT_SYMBOL_NAME" --watch 30
```

## What output we need

Please keep these fields:

- symbol name
- digits
- point
- trade_tick_size
- trade_tick_value
- trade_contract_size
- volume_min
- volume_max
- volume_step
- trade_stops_level
- filling_mode
- order_mode
- one or two sample ticks

Do not share your login or password.

## Next step

After the actual BRA50 specification is known, Step 2 will introduce a runtime instrument configuration and a small FastAPI endpoint:

- `/api/status`
- `/api/symbol/BRA50`
- `/api/tick/BRA50`

Still read-only.
