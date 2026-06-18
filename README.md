# Renko Analysis

Python project for financial market analysis and Renko chart generation from tick-by-tick data.

## Overview

Renko Analysis is a market data processing engine designed to transform raw tick data into Renko structures suitable for quantitative research, statistical analysis and trading strategy development.

The project uses MetaTrader 5 as a data source and stores both tick and Renko data in SQLite databases.

## Features

* Tick collection from MetaTrader 5
* Tick normalization and processing
* SQLite persistence layer
* Instrument configuration system
* Renko brick generation
* Multi-brick processing
* Renko state management
* Renko persistence layer
* Renko plotting dataframe generation

## Project Structure

```text
renko-analysis/
├── ingestion/
├── market/
├── renko/
├── storage/
├── docs/
├── scripts/
└── main.py
```

## Technologies

* Python
* Pandas
* SQLite
* MetaTrader 5
* Matplotlib
* MPLFinance

## Roadmap

* [x] Tick collection
* [x] Tick persistence
* [x] Renko generation
* [x] Renko state management
* [x] Multi-brick processing
* [ ] Renko visualization
* [ ] Statistical analysis
* [ ] Pattern detection
* [ ] Backtesting engine

## Author

Danilo Silli
