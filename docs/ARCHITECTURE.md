# Renko Analysis — Architecture

## 1. Purpose

This document describes the current architecture of the Renko Analysis project.

The objective is to document how the system works today before making structural changes to the project.

This document describes the **current architecture (AS-IS)**. It does not yet define the final target architecture.

---

## 2. System Overview

Renko Analysis is a Python application for collecting market data from MetaTrader 5, storing tick data, generating Renko bricks, processing intraday and realtime market data, and supporting trading operations based on Renko information.

The project currently contains historical, intraday and realtime processing flows.

At a high level, the system contains the following areas:

* market data ingestion from MetaTrader 5;
* tick normalization and representation;
* historical and intraday persistence;
* Renko generation;
* realtime Renko processing;
* trading rules and operation management;
* API and web interface;
* diagnostic and maintenance utilities.

---

## 3. Main Entry Points

### 3.1 `main.py`

`main.py` is the current manual entry point for historical market processing.

Its main responsibilities are:

* select one or more symbols;
* select one or more historical dates;
* connect to MetaTrader 5;
* collect historical ticks;
* normalize collected ticks;
* persist historical tick data;
* generate historical Renko bricks;
* persist generated Renko data.

The script currently supports the following execution modes:

* `collect_only`
* `renko_only`
* `collect_and_renko`

The dates and symbols are currently configured manually in the source code.

Conceptual flow:

```text
Selected symbol/date
        |
        v
MT5Client
        |
        v
TickCollector
        |
        v
Tick normalization
        |
        v
TickRepository
        |
        v
Historical tick database
        |
        v
RenkoEngine
        |
        v
RenkoRepository
        |
        v
Historical Renko database
```

`main.py` is an operational tool and is not currently the realtime application entry point.

---

### 3.2 `api/app.py`

`api/app.py` is the main entry point for the realtime/web application.

It currently has responsibilities related to:

* FastAPI application initialization;
* MT5 configuration;
* historical/intraday bootstrap;
* realtime market feeds;
* WIN and CFD processing;
* intraday market pipelines;
* Renko services and runtimes;
* source handoff;
* repositories and persistence;
* trading runtime initialization;
* trading signals;
* order validation;
* operation management;
* broker routing;
* API endpoints;
* frontend integration.

Because the project evolved incrementally, `api/app.py` currently acts both as an API entry point and as a major application composition/orchestration point.

This responsibility will be analyzed later before deciding whether it should be divided into smaller components.

No structural change is defined by this document yet.

---

## 4. Current Project Areas

The project is currently divided into the following main directories.

### `ingestion/`

Contains components responsible for obtaining market data, especially from MetaTrader 5.

Examples include:

* MT5 clients;
* realtime feed workers;
* intraday historical data retrieval;
* tick collection;
* tick transformation and utilities.

---

### `market/`

Contains market-domain data structures and instrument configuration.

Current examples include:

* instrument configuration;
* intraday tick representation;
* realtime tick representation.

---

### `renko/`

Contains the core structures and logic related to Renko processing.

Current components include:

* Renko bricks;
* Renko engine;
* Renko state.

The exact dependencies between the Renko engine and persistence components will be documented during the architecture audit.

---

### `services/`

Contains services responsible for coordinating multiple components and processing flows.

Current responsibilities include:

* market processing;
* Renko services;
* historical tick adaptation;
* intraday bootstrap;
* intraday market pipelines;
* intraday/realtime adapters;
* dual MT5 feeds;
* source handoff.

The boundary between orchestration services and domain logic will be analyzed later.

---

### `storage/`

Contains persistence-related components.

Current responsibilities include:

* SQLite access;
* tick repositories;
* Renko repositories;
* historical/intraday/realtime persistence;
* trading operation persistence.

The project currently uses multiple SQLite databases for different types of information.

The database architecture will be documented separately.

---

### `trading/`

Contains the current trading-domain components.

Current components include:

* broker routing;
* operation management;
* order validation/guard;
* Renko 30R signal logic;
* trading operation representation;
* trading service.

Trading rules must remain separated from architectural refactoring whenever possible so structural changes do not unintentionally modify trading behavior.

---

### `api/`

Contains the FastAPI application, API routers and schemas used by the web/realtime application.

The current `api/app.py` also performs significant application initialization and orchestration.

---

### `web/`

Contains the current web interface used with the realtime application.

Its architecture will be documented separately after the backend flow is understood.

---

### `scripts/`

Contains manually executed utilities, diagnostics and older validation programs.

The directory currently mixes different types of scripts.

A future organization may distinguish:

* diagnostics;
* maintenance;
* operational utilities;
* manual validation.

No files will be moved until their purpose has been reviewed.

---

### `tests/`

Contains automated and semi-integrated validation of multiple parts of the system.

The current test collection includes different categories such as:

* unit-like tests;
* repository/database tests;
* MT5 integration tests;
* historical/intraday tests;
* realtime runtime tests;
* trading tests.

Some tests require external conditions such as an MT5 connection or available market data.

The test architecture will be reviewed separately.

---

## 5. Manual Maintenance and Diagnostic Tools

The project currently contains several manually executed files outside the normal application runtime.

These include files used for:

* SQLite database maintenance;
* Renko data manipulation;
* MT5 diagnostics;
* investigation of orders, deals, positions and tickets;
* manual runtime validation.

Examples currently include:

* `test`
* `insert_renko.py`
* `diagnose_mt5_ticket_relation.py`
* `test_position_ticket_from_deal.py`
* diagnostic scripts under `scripts/`

These files must not be considered obsolete solely because they are manually executed.

Their purpose will be documented before they are renamed, moved, divided or removed.

---

## 6. Architecture Review Principle

The project will be reorganized incrementally.

Before changing a component:

1. document its current responsibility;
2. identify its dependencies;
3. determine whether the current location is appropriate;
4. identify existing tests;
5. define the proposed change;
6. review the proposal;
7. implement only the approved change;
8. run the relevant tests;
9. commit the change separately.

Architecture refactoring should not intentionally change trading rules or Renko behavior unless that behavioral change is explicitly part of the task.

---

## 7. Areas Still to Be Documented

The following areas require further analysis before this architecture document is considered complete:

* historical data flow;
* intraday bootstrap flow;
* realtime market flow;
* XP and ActivTrades source responsibilities;
* WIN and CFD runtime relationship;
* source handoff;
* Renko runtime lifecycle;
* persistence architecture;
* database schemas;
* trading execution flow;
* API architecture;
* frontend architecture;
* automated test architecture;
* diagnostic and maintenance tooling.

These sections will be added incrementally as each part of the system is reviewed.
