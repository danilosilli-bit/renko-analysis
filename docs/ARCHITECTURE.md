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

## 10. Trading Architecture

The trading subsystem currently implements a semi-automatic execution model.

Trade entry is initiated manually by the user through the application.

Renko signals do not automatically create market orders.

Instead, the current 30R Renko signal acts as an authorization mechanism that determines whether a manually requested BUY or SELL operation is allowed.

The current architectural refactoring must preserve this behavior.

---

### 10.1 Semi-Automatic Trading Model

The current trading model is:

```text
User decides to enter
        |
        v
Manual BUY / SELL request
        |
        v
TradingService
        |
        v
OrderGuard
        |
        v
30R Renko authorization
        |
   +----+----+
   |         |
blocked    allowed
             |
             v
      TradingOperation
             |
             v
        MT5 execution
```

The system therefore separates:

```text
ENTRY DECISION
    made manually by the user

        from

ENTRY AUTHORIZATION
    determined by the platform
    using the current trading rules
```

A closed Renko brick does not automatically create an order.

---

### 10.2 30R Trading Signal

The current operational signal is based on the latest closed 30R Renko brick.

Conceptually:

```text
Latest 30R brick UP
        |
        +--> BUY may be authorized
        |
        +--> SELL is blocked


Latest 30R brick DOWN
        |
        +--> SELL may be authorized
        |
        +--> BUY is blocked
```

The signal also determines the maximum stop boundary associated with the entry.

The current implementation uses the latest 30R brick when calculating this boundary.

The 30R signal is an authorization mechanism.

It is not an automatic order generator.

---

### 10.3 OrderGuard

`OrderGuard` protects new entries.

Before an entry order is sent to the broker, the requested direction must be compatible with the current operational signal.

The guard follows a fail-closed principle.

If the platform cannot safely determine that the requested entry is allowed, the entry must not proceed.

Examples include situations where:

* no valid trading signal is available;
* the Renko state is not ready;
* the requested direction conflicts with the signal;
* the signal evaluation fails;
* the required guard is unavailable.

The purpose of the guard is to prevent execution when the platform cannot positively authorize the operation.

---

### 10.4 Broker Routing

`BrokerRouter` separates the logical trading request from the broker/feed used to execute it.

The current system supports distinct trading destinations associated with the WIN and CFD runtimes.

Conceptually:

```text
Trading request
      |
      v
BrokerRouter
   +--+--+
   |     |
   v     v
  XP   ActivTrades
  |       |
 WIN     CFD
```

This separation must be preserved because WIN and CFD represent independent runtime and execution paths.

---

### 10.5 TradingOperation

`TradingOperation` represents the platform's logical trading operation.

The logical operation is distinct from the MT5 order and position identifiers.

Conceptually:

```text
TradingOperation
      |
      +--> operation_id
      |
      +--> broker/feed
      |
      +--> symbol
      |
      +--> side
      |
      +--> volume
      |
      +--> entry information
      |
      +--> max_stop_price
      |
      +--> current_stop_price
      |
      +--> mt5_order_ticket
      |
      +--> mt5_position_ticket
      |
      +--> operation status
```

This allows the platform to maintain its own operation identity independently from broker-specific identifiers.

The logical operation should remain the central representation of a trade managed by the platform.

---

### 10.6 Operation Lifecycle

The current operation lifecycle includes states such as:

```text
             create
               |
               v
            PENDING
           /       \
          /         \
         v           v
      FAILED      RECONCILE
         |
         | successful execution
         v
        OPEN
         |
         | confirmed close
         v
       CLOSED
```

The exact transition depends on the result of broker execution and reconciliation.

`RECONCILE` is important for situations where the platform cannot safely determine the final broker state.

For example, a timeout or ambiguous MT5 result must not automatically be interpreted as either successful execution or definite failure.

The platform should preserve the uncertainty until reconciliation can establish the actual broker state.

---

### 10.7 OperationManager

`OperationManager` manages the lifecycle of logical trading operations.

Its responsibilities currently include operations such as:

* creating logical operations;
* maintaining active operations;
* updating operation state;
* associating broker identifiers with logical operations;
* updating the current stop representation;
* persisting operation changes through the trading repository.

The manager provides a boundary between the trading workflow and persistence of the logical operation state.

---

### 10.8 Trading Persistence

Trading operations are persisted separately from market tick and Renko persistence.

The trading persistence layer stores the logical state required to reconstruct and manage operations.

An important current invariant is that:

```text
max_stop_price
```

is established when the operation is created and is not subsequently modified by normal operation updates.

By contrast:

```text
current_stop_price
```

represents the stop value that may evolve during the lifetime of the operation.

This distinction is intentional and must be preserved.

---

### 10.9 Maximum Stop and Current Stop

The current logical model contains two distinct stop concepts.

#### Maximum Stop

`max_stop_price` represents the maximum allowed risk boundary established when the operation is created.

It is immutable during the normal lifetime of the operation.

Conceptually:

```text
ENTRY
  |
  v
max_stop_price established
  |
  v
FIXED FOR THE OPERATION
```

The maximum stop acts as a risk boundary and must not be moved in a direction that increases the allowed risk.

#### Current Stop

`current_stop_price` represents the operational stop value managed by the platform.

It may evolve during the lifetime of the operation, subject to the maximum-stop boundary and the operation's stop movement rules.

Conceptually:

```text
BUY operation

max_stop_price
      |
      | permitted range
      v
current_stop_price
      |
      | may move upward
      v
future protective levels
```

For SELL operations, the direction is reversed accordingly.

The current logical rules prevent the current stop from being moved in a direction that increases risk beyond the permitted boundary.

---

### 10.10 Stop Execution Status

The logical stop model must not be confused with broker-side stop execution.

At the current stage of the project:

```text
max_stop_price
      |
      +--> represented by the platform

current_stop_price
      |
      +--> represented and controlled logically
           by the platform
```

The complete mechanism that sends and manages these operational stop orders in MT5 has **not yet been implemented**.

Therefore:

```text
logical stop state
        !=
complete MT5 stop-order management
```

Architectural refactoring must not silently introduce broker-side stop behavior.

---

### 10.11 Future MT5 Safety Stop

A separate broker-side safety stop has been identified as a future requirement.

The intention is that a protective stop may eventually be placed directly in MT5 immediately after entry so that some broker-side protection exists even if the application becomes unavailable.

Conceptually, the future model may contain three related but distinct concepts:

```text
TradingOperation
      |
      +--> max_stop_price
      |      immutable logical risk boundary
      |
      +--> current_stop_price
      |      platform-managed operational stop
      |
      +--> MT5 safety stop
             broker-side protection
```

The behavior, calculation and lifecycle of the MT5 safety stop have not yet been defined.

It must therefore not be implemented as part of the current architectural reorganization.

---

### 10.12 Future Position Management

Additional position-management capabilities are planned but are not part of the current implementation.

They include concepts such as:

* moving the operational stop;
* break-even;
* partial exits;
* future stop-management rules;
* sending and modifying stop orders in MT5.

These are future functional developments.

The current architecture work should make these capabilities easier to implement later, but must not implement or define their trading rules prematurely.

---

### 10.13 Current Trading Responsibilities

The current trading subsystem is divided approximately as follows:

```text
renko_30r_signal.py
        |
        +--> operational signal calculation
        +--> entry direction authorization data
        +--> maximum stop boundary information


order_guard.py
        |
        +--> entry protection
        +--> signal validation
        +--> allow / block decision


trading_operation.py
        |
        +--> logical operation model
        +--> operation invariants
        +--> stop invariants


operation_manager.py
        |
        +--> operation lifecycle
        +--> active operation management
        +--> logical state updates
        +--> persistence coordination


broker_router.py
        |
        +--> broker/feed routing


trading_service.py
        |
        +--> trading workflow orchestration
        +--> validation
        +--> guard coordination
        +--> logical operation creation
        +--> broker communication
        +--> broker result interpretation
        +--> operation state transitions


trading_operation_repository.py
        |
        +--> persistent storage of logical operations
```

This separation already provides useful architectural boundaries.

---

### 10.14 Current Architecture Observation

The primary architectural concern in the trading subsystem is not the existing trading behavior.

The main concern is the potential growth of `TradingService`.

`TradingService` currently coordinates several parts of the execution workflow.

This is manageable with the current feature set, but future functionality such as:

```text
MT5 safety stop
operational stop updates
break-even
partial exits
position reconciliation
additional risk rules
```

could significantly increase its responsibilities.

A future refactoring may therefore consider separating some orchestration responsibilities into dedicated components.

No such refactoring decision has been made yet.

The architecture should first be reorganized without changing trading behavior.

---

### 10.15 Protected Trading Invariants

The following behaviors must be preserved during the current architectural reorganization:

1. The system remains semi-automatic.

2. Entry orders are initiated manually by the user.

3. Closing a Renko brick does not automatically create an entry order.

4. The 30R Renko signal authorizes or blocks a manually requested entry.

5. Entry validation follows a fail-closed approach.

6. WIN and CFD execution paths remain independently routed to their corresponding brokers/feeds.

7. The platform maintains a logical `TradingOperation` identity independently from MT5 tickets.

8. Ambiguous broker execution states may enter `RECONCILE` rather than being incorrectly assumed successful or failed.

9. `max_stop_price` is established for the operation and remains immutable.

10. `current_stop_price` may evolve only according to the operation's risk constraints.

11. Existing logical stop fields must not be interpreted as complete MT5 stop-order management.

12. MT5 safety stop, break-even, automatic stop movement and partial exits are future functionality and must not be implemented as side effects of the current refactoring.

13. The objective of the current refactoring is structural clarity and maintainability, not new trading behavior.

## 11. Persistence Architecture

The application currently maintains separate persistence areas for different data lifecycles.

These persistence areas must not be interpreted as redundant copies of the same database.

They serve different operational purposes and have different lifecycle and safety requirements.

The current architecture can be divided conceptually into:

```text
Historical Staging
        |
        | manual validation and promotion
        v
Historical Approved
        |
        | bootstrap
        v
Intraday Runtime

Trading Persistence
        |
        +--> independent persistent lifecycle
```

The current architectural refactoring must preserve these lifecycle boundaries.

---

### 11.1 Historical Staging

Historical market data is initially collected and processed through the manual historical workflow implemented by `main.py`.

The staging databases are currently:

```text
data/ticks.db
data/renko.db
```

Conceptually:

```text
MT5 historical data
        |
        v
main.py
        |
        +--> collect and normalize ticks
        |
        v
data/ticks.db
        |
        +--> historical Renko processing
        |
        v
data/renko.db
```

These databases represent a historical staging area.

They are used to produce and inspect historical data before that data becomes part of the historical dataset used by the realtime application.

They must not be considered obsolete solely because equivalent database names also exist under `data/historical/`.

---

### 11.2 Historical Validation and Promotion

Promotion from historical staging to the approved historical dataset is currently a deliberate manual process.

Conceptually:

```text
data/ticks.db
data/renko.db
        |
        v
manual inspection / validation
        |
        v
manual copy
        |
        v
data/historical/ticks.db
data/historical/renko.db
```

This manual step acts as a validation barrier.

Its purpose is to prevent newly collected or newly processed historical data from immediately replacing the historical dataset used by the runtime before the data has been checked.

This behavior is intentional.

The current architectural refactoring must not automatically make `main.py` write directly to the approved historical databases.

Any future automation of historical promotion would be a separate functional change requiring explicit design and validation.

---

### 11.3 Historical Approved Data

The approved historical persistence area is:

```text
data/historical/
    ticks.db
    renko.db
```

This area represents historical data that has passed the current manual validation process.

The realtime application may rely on this data when reconstructing the current Renko state.

Conceptually:

```text
Historical Staging
        |
        | validation
        v
Historical Approved
        |
        v
Runtime Bootstrap
```

The distinction between staging and approved historical data is therefore a safety boundary, not accidental duplication.

---

### 11.4 Intraday Persistence

Intraday runtime data is stored separately under:

```text
data/intraday/
    ticks.db
    renko.db
```

This persistence belongs to the current runtime/session lifecycle.

Realtime market ticks are persisted through the intraday pipeline and realtime Renko bricks are persisted through the intraday Renko persistence path.

Conceptually:

```text
Realtime market feed
        |
        v
IntradayMarketPipeline
        |
        +--> data/intraday/ticks.db
        |
        v
RenkoService
        |
        +--> data/intraday/renko.db
```

Intraday persistence is intentionally separated from approved historical persistence.

---

### 11.5 Reconstructible Intraday State

Intraday persistence is reconstructible.

At application startup, the intraday storage may be reset without deleting the approved historical dataset.

The runtime can reconstruct its starting point using:

```text
Approved historical Renko state
        +
Current-day bootstrap data
        |
        v
Current runtime state
```

Therefore, the lifecycle of intraday persistence differs fundamentally from the lifecycle of historical approved data.

Resetting intraday storage must not imply resetting or modifying:

```text
data/historical/*
data/trading/*
```

---

### 11.6 Historical-to-Intraday Boundary

The realtime Renko persistence path intentionally bridges historical and intraday lifecycles.

Conceptually:

```text
READ INITIAL STATE

data/historical/renko.db
        |
        v
historical state / last closed brick
        |
        v
bootstrap
        |
        v
runtime


WRITE CURRENT SESSION

runtime
        |
        v
current-day Renko bricks
        |
        v
data/intraday/renko.db
```

This is an intentional dependency.

The runtime uses approved historical data as its trusted starting point while keeping current-session persistence separate.

---

### 11.7 Trading Persistence

Trading state has its own persistence lifecycle:

```text
data/trading/trading.db
```

Trading persistence stores logical trading operations managed by the platform.

Conceptually:

```text
TradingService
        |
        v
OperationManager
        |
        v
TradingOperationRepository
        |
        v
data/trading/trading.db
```

Unlike intraday market persistence, trading state must not be treated as disposable runtime cache.

Trading operations may need to survive application restarts and preserve their logical identity and execution state.

---

### 11.8 Persistence Domain Separation

The current persistence model maintains useful domain boundaries:

```text
HISTORICAL STAGING
    production and validation
          |
          v
HISTORICAL APPROVED
    trusted historical source
          |
          v
INTRADAY
    reconstructible runtime data


TRADING
    persistent operation state
```

Market/Renko persistence and trading-operation persistence serve different purposes.

The architecture should avoid introducing unnecessary coupling such as storing trading operations inside intraday market databases or storing Renko market state inside the trading database.

---

### 11.9 Database Lifecycle Summary

The current lifecycle can be summarized as:

```text
data/ticks.db
data/renko.db
    |
    | Historical staging
    | Produced manually through main.py
    | Validated before promotion
    v

data/historical/ticks.db
data/historical/renko.db
    |
    | Approved historical data
    | Trusted by runtime bootstrap
    v

data/intraday/ticks.db
data/intraday/renko.db
    |
    | Current runtime/session
    | Reconstructible
    v

data/trading/trading.db
    |
    | Logical trading operations
    | Persistent across runtime sessions
    v
```

The four lifecycle roles are therefore:

```text
STAGING
    temporary production/validation area

APPROVED HISTORICAL
    trusted historical source

INTRADAY
    reconstructible current-session state

TRADING
    persistent operation state
```

---

### 11.10 Current Architecture Observation

The current persistence separation is broadly aligned with the application's operational requirements.

No major persistence redesign is currently required.

In particular, the existence of:

```text
data/ticks.db
data/renko.db
```

together with:

```text
data/historical/ticks.db
data/historical/renko.db
```

is intentional.

The first pair represents historical staging.

The second pair represents manually validated historical data approved for runtime use.

Future architecture work may improve naming, configuration or encapsulation around these persistence areas, but such changes must preserve their lifecycle semantics.

Refactoring should not remove a persistence boundary merely to reduce the number of database files.

---

### 11.11 Protected Persistence Invariants

The following persistence behaviors must be preserved during the current architectural reorganization:

1. `main.py` remains a manual historical collection and Renko-processing tool.

2. Historical data produced by `main.py` remains separate from the approved historical dataset until validation occurs.

3. Promotion from historical staging to approved historical data remains manual during the current refactoring.

4. The current refactoring must not cause `main.py` to overwrite approved historical databases directly.

5. `data/historical/` remains the trusted historical source used by the runtime bootstrap.

6. Intraday persistence remains separate from approved historical persistence.

7. Intraday state remains reconstructible from approved historical state and current-day market data.

8. Resetting intraday storage must not delete or reset approved historical data.

9. Resetting intraday storage must not delete or reset trading-operation persistence.

10. Trading persistence remains logically separate from market tick and Renko persistence.

11. Trading operations must not be treated as disposable intraday state.

12. Architectural reorganization must preserve the distinct lifecycle semantics of staging, approved historical, intraday and trading persistence.

13. Automating historical validation or promotion is outside the scope of the current architectural refactoring.
