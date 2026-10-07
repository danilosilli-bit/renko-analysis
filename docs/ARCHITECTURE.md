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

## 8. Historical Processing Flow

The historical processing flow is currently started manually through `main.py`.

Its purpose is to collect historical market ticks from MetaTrader 5 and/or generate historical Renko bricks from previously stored ticks.

### 8.1 Execution Modes

`main.py` currently supports three execution modes:

* `collect_only`
* `renko_only`
* `collect_and_renko`

This allows tick collection and Renko generation to be executed independently or sequentially.

Symbols, dates and execution parameters are currently configured manually in `main.py`.

---

### 8.2 Historical Tick Collection

The historical tick collection flow is:

```text
main.py
   |
   v
MT5Client
   |
   v
TickCollector
   |
   v
tick_transformer.normalize_ticks()
   |
   v
TickRepository
   |
   v
Historical tick database
```

Responsibilities:

#### `MT5Client`

Provides access to MetaTrader 5 historical tick data.

Its responsibility is primarily communication with MT5.

#### `TickCollector`

Coordinates historical tick collection for the requested symbol and time period.

#### `tick_transformer`

Normalizes and enriches collected tick data before persistence.

Current processing includes operations related to:

* timestamp normalization;
* duplicate handling;
* volume filtering;
* buy/sell quantities;
* financial values;
* auction-related information.

#### `TickRepository`

Persists and retrieves historical tick data using SQLite.

---

### 8.3 Historical Renko Generation

Historical Renko generation uses ticks previously persisted in the historical tick database.

The current flow is:

```text
Historical tick database
        |
        v
TickRepository
        |
        v
InstrumentConfig
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

#### `InstrumentConfig`

Provides instrument-specific configuration required by Renko processing, including information such as tick size, price precision and configured Renko sizes.

#### `RenkoEngine`

Processes the historical tick sequence and generates Renko bricks according to the configured instrument and Renko size.

The current engine also interacts directly with a Renko repository for persistence.

This dependency is part of the current architecture and will be reviewed later. No change is currently planned.

#### `RenkoRepository`

Persists historical Renko bricks and associated Renko state.

---

### 8.4 Current Historical Flow Assessment

The historical flow currently has reasonably separated responsibilities for:

* MT5 access;
* tick collection;
* tick transformation;
* tick persistence;
* instrument configuration;
* Renko processing;
* Renko persistence.

The current `main.py` combines execution configuration and orchestration.

For example, symbols, dates and execution modes are currently defined directly in the source code.

This works for the current manual workflow but may later be replaced by command-line parameters or another configuration mechanism.

No change is required at this stage.

---

### 8.5 Known Architecture Observation

`RenkoEngine` currently knows about Renko persistence through a repository.

Conceptually, the current relationship includes:

```text
RenkoEngine
    |
    +-- Renko generation logic
    |
    +-- Renko persistence interaction
```

A possible future architecture could separate Renko generation from persistence orchestration.

However, `RenkoEngine` participates in multiple processing flows, including historical, intraday and realtime processing.

For this reason, this dependency must only be reconsidered after those flows have also been documented and understood.

No refactoring decision has been made.

## 9. Bootstrap, Runtime Bifurcation and Realtime Flow

The application uses a bootstrap process to reconstruct the current intraday Renko state before starting independent WIN and CFD realtime runtimes.

This behavior is intentional and is a **functional requirement of the system**.

Architectural refactoring must preserve this processing sequence unless a behavioral change is explicitly requested.

---

### 9.1 Bootstrap Starting State

The bootstrap process does not start the Renko engines from an empty state.

For each configured Renko size, the application restores the previously persisted historical state and the last closed Renko brick.

The currently relevant Renko sizes are:

* 10R
* 30R
* 45R

Conceptually:

```text
Historical Renko state
        +
Last closed Renko brick
        |
        v
Bootstrap RenkoService
```

This establishes the starting point for processing the current trading day.

---

### 9.2 Current-Day Bootstrap

After restoring the previous Renko state, the application obtains the current day's WIN ticks from the XP MetaTrader 5 source.

The bootstrap flow is:

```text
Historical Renko state
        |
        v
Bootstrap RenkoService
        |
        v
Current-day XP / WIN ticks
        |
        v
IntradayTick conversion
        |
        v
Renko processing
        |
        v
Updated 10R / 30R / 45R state
```

The current-day ticks are replayed in chronological order to reconstruct the Renko state up to the end of the bootstrap data.

During this replay, persistence is intentionally deferred where appropriate so the bootstrap can reconstruct the runtime state without treating the replay as ordinary realtime processing.

---

### 9.3 Runtime Snapshot

After the current-day bootstrap is complete, the application creates a runtime snapshot.

The snapshot contains the information required to continue each Renko size from the same reconstructed point, including:

* Renko state;
* last closed brick.

The snapshot creates independent copies of the runtime state.

Conceptually:

```text
Bootstrap state
  10R / 30R / 45R
        |
        v
Runtime Snapshot
```

This snapshot is the common starting point for the WIN and CFD realtime runtimes.

---

### 9.4 WIN and CFD Bifurcation

After the snapshot is created, the application bifurcates the processing into two independent Renko runtimes.

```text
                  Bootstrap
                     |
                  Snapshot
                     |
              +------+------+
              |             |
              v             v
          WIN Runtime    CFD Runtime
```

Both runtimes begin from the same reconstructed market history.

After bifurcation, however, their Renko states are independent.

Changes to one runtime must not mutate the state of the other runtime.

This independence is an intentional requirement of the system.

---

### 9.5 WIN Realtime Runtime

After bifurcation, the WIN runtime continues using realtime market data from the XP MetaTrader 5 source.

Conceptually:

```text
Bootstrap Snapshot
        |
        v
WIN RenkoService
        |
        v
XP / WIN realtime ticks
        |
        v
WIN IntradayMarketPipeline
        |
        +----> Intraday tick persistence
        |
        v
WIN Renko processing
```

The WIN runtime continues independently from the common bootstrap snapshot.

---

### 9.6 CFD Realtime Runtime

The CFD runtime also starts from the common bootstrap snapshot.

After bifurcation, however, it continues using realtime market data from the ActivTrades MetaTrader 5 source.

Conceptually:

```text
Bootstrap Snapshot
        |
        v
CFD RenkoService
        |
        v
ActivTrades / CFD realtime ticks
        |
        v
CFD IntradayMarketPipeline
        |
        +----> Intraday tick persistence
        |
        v
CFD Renko processing
```

The CFD runtime therefore shares the reconstructed past with the WIN runtime but has an independent realtime future.

---

### 9.7 Source Handoff

The transition between bootstrap data and realtime data is explicitly represented by the source handoff mechanism.

`SourceHandoffService` identifies the first realtime tick following the bootstrap and marks the source transition.

This is especially relevant to the CFD runtime because its historical/current-day bootstrap originates from the WIN/futures data flow while its realtime continuation uses the CFD source.

Conceptually:

```text
Bootstrap source
      |
      v
Last bootstrap tick
      |
      | source handoff
      v
First realtime tick
      |
      v
Realtime source
```

The source transition is intentional and must remain identifiable by the runtime.

---

### 9.8 Dual Realtime MT5 Feed

Realtime data is currently obtained through `DualMT5FeedService`.

The service manages independent MT5 feed workers for the WIN and CFD sources.

Conceptually:

```text
                 DualMT5FeedService
                         |
              +----------+----------+
              |                     |
              v                     v
        XP / WIN worker      ActivTrades / CFD worker
              |                     |
              +----------+----------+
                         |
                         v
                       Queue
                         |
                         v
                  Runtime consumer
                    +----+----+
                    |         |
                    v         v
                  WIN        CFD
                callback   callback
```

The feed workers are responsible for obtaining realtime ticks.

Renko processing remains outside the feed workers.

---

### 9.9 Realtime Market Pipelines

After routing to the correct runtime, each realtime tick passes through its corresponding `IntradayMarketPipeline`.

The pipeline is responsible for:

1. converting the realtime tick into the intraday representation;
2. persisting the intraday tick;
3. forwarding the tick to the corresponding `RenkoService`.

The two runtime paths remain independent:

```text
XP realtime
    |
    v
WIN pipeline
    |
    v
WIN RenkoService


ActivTrades realtime
    |
    v
CFD pipeline
    |
    v
CFD RenkoService
```

---

### 9.10 Protected Runtime Invariants

The following behavior is considered a functional requirement and must be preserved during architectural refactoring:

1. Renko bootstrap starts from the previously persisted historical state rather than from an empty state.

2. Current-day XP/WIN ticks are replayed before runtime bifurcation.

3. The bootstrap produces a common reconstructed Renko state for 10R, 30R and 45R.

4. WIN and CFD runtimes are initialized from the same runtime snapshot.

5. After bifurcation, WIN and CFD Renko states are independent.

6. WIN realtime processing continues from the XP/WIN source.

7. CFD realtime processing continues from the ActivTrades/CFD source.

8. The transition between bootstrap and realtime sources remains explicitly identifiable.

9. Architectural refactoring must not change these behaviors unless the behavioral change is explicitly designed, reviewed and tested.

---

### 9.11 Current Architecture Observation

The bootstrap, bifurcation and realtime processing model matches the intended system behavior.

No redesign of this processing logic is currently planned.

The main architectural concern is that a significant portion of the initialization and orchestration of this flow currently resides in `api/app.py`.

A future architecture review may consider moving orchestration responsibilities into dedicated application services or runtime components.

Such a change would concern **where the orchestration is implemented**, not **how the bootstrap, bifurcation and realtime behavior works**.

No refactoring decision has been made at this stage.
