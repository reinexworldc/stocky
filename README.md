# Stocky

![Alt text](stocky-gif.gif)

## Product in One Sentence

An agent that reviews your entire warehouse every day, understands what's happening, and tells the owner or procurement manager exactly what needs to be done today — in plain human language, not spreadsheets.

## What This Product Is

`Stocky` is an AI agent for managing inventory, procurement, and product-level risks.
It connects to warehouse, sales, supplier, and order data, then independently identifies problems, calculates priorities, and suggests specific actions.

The core idea: a person shouldn't have to manually review dozens of reports, export stock levels, cross-reference sales, and try to figure out what to order, what to liquidate, and where there's already a risk of lost revenue.
The agent does this work.

The output is not just numbers, but ready-made decisions:

- what needs to be ordered first;
- which supplier is the best option;
- what order volume to place;
- which products are about to go out of stock;
- which items are stagnant and freezing capital;
- why the agent reached that particular conclusion.

## Who This Product Is For

The product is designed for:

- e-commerce or retail business owners;
- procurement managers;
- operations managers;
- warehouse managers;
- category managers.

Especially useful where the SKU count is already high, decisions need to be made quickly, and manual analysis is starting to slow down growth.

## What Problem the Agent Solves

The typical procurement and inventory control process looks like this:

- someone manually opens stock levels;
- separately reviews sales history;
- separately checks suppliers and lead times;
- tries to figure out what's running low;
- tries not to over-order;
- then manually assembles a supplier order.

This is slow, noisy, and often leads to mistakes:

- key products run out too early;
- capital gets frozen in dead stock;
- orders are placed too late;
- products are ordered from the wrong supplier;
- decisions depend on a specific person's experience rather than a systematic process.

`Stocky` turns this chaos into a clear daily management loop:

- analyzes the entire catalog;
- identifies risks;
- forecasts demand;
- suggests purchases;
- generates orders;
- explains its actions in plain language.

## Primary Use Case

A typical user question:

`What do I need to order this week?`

Instead of a generic answer, the agent runs a full workflow chain:

1. analyzes the entire catalog;
2. finds critical and borderline items;
3. performs a detailed analysis of problematic SKUs;
4. evaluates demand and sales velocity;
5. calculates the recommended purchase volume;
6. groups purchases by supplier;
7. returns a clear action list with explanations.

As a result, the user gets not a report, but a ready-to-go operational plan for the week.

## Agent Tools

Below is the complete list of tools the agent uses within the product.

### `analyze_full_catalog`

Reviews all SKUs simultaneously and ranks them by criticality.

What it does:

- analyzes the entire assortment at once, not one product at a time;
- compares current stock, sales velocity, safety stock, and lead times;
- identifies items where stockout risk is highest;
- identifies items where everything is fine and no intervention is needed;
- compiles a ranked action list.

What it returns:

- red items — critical, immediate action required;
- yellow items — action will be needed soon;
- green items — stock situation is stable.

Why it's needed:

This is the main entry tool for a system-wide overview. It helps avoid drowning in a large catalog and immediately understand where the real risks are versus noise.

## TODO: Real-Time Event Feed Architecture

A framework for a future real-time `Event Feed` has been added to the project, but the logic is not yet implemented.

Current state:

- created the `app/services/event_stream.py` module;
- added dataclass models for trigger, context, decision, and final event record;
- added empty orchestration functions with `TODO` and `NotImplementedError`;
- module exported through `app/services/__init__.py`.

Why it's needed:

- separate event detection from the UI;
- don't tie the event feed to a static snapshot analysis;
- prepare a layer for real-time and near-real-time warehouse signals;
- later connect the LLM only for explanation and event wording, not for all business logic.

Planned pipeline:

1. incoming warehouse change -> `build_inventory_event_trigger(...)`;
2. load current and previous state -> `load_inventory_event_context(...)`;
3. find meaningful pattern -> `detect_inventory_event_patterns(...)`;
4. rule-based score / priority -> `score_inventory_event_priority(...)`;
5. decide whether to show the event at all -> `decide_inventory_event_emission(...)`;
6. generate human-readable event text -> `build_inventory_event_prompt(...)` and `generate_inventory_event_copy(...)`;
7. persist -> `persist_inventory_event(...)`;
8. deliver to UI / feed / websocket -> `publish_inventory_event(...)`.

Planned event types:

- new shipment received when stock is already high;
- sharp week-over-week demand increase;
- sharp demand slowdown;
- stockout risk earlier than forecast;
- product transitioning to overstock / dead-stock risk;
- no sales after recent replenishment;
- abnormally fast consumption for a SKU;
- recommendation event: purchase, discount, promotion, bundle, stop reorder.

What remains to be done:

- connect event source from warehouse operations, sales, and shipments;
- add snapshot comparison / previous-state lookup;
- define rule-based triggers and cooldown/deduplication;
- add storage for event records;
- choose transport for real-time delivery to UI;
- connect the LLM layer only for human-readable summary/headline/recommendation;
- replace the current static event feed with a stream of generated inventory events.

Mathematical logic:

- `total_qty = sum(stock.quantity across all warehouses)`
- `reserved_qty = sum(stock.reserved_qty across all warehouses)`
- `available_qty = total_qty - reserved_qty`
- `velocity_7d = sold_last_7_days / 7`
- `reorder_point_days = lead_time_days + safety_stock_days`
- `days_of_stock = available_qty / max(velocity_7d, epsilon)`
- `reorder_qty = max(0, target_stock - available_qty)`

Rough rule-based classification for MVP:

- `critical` if `days_of_stock <= lead_time_days`
- `warning` if `lead_time_days < days_of_stock <= reorder_point_days`
- `ok` if `days_of_stock > reorder_point_days`
- `dead_stock` if sales are negligible and `dead_stock_days` exceeds the threshold
- `overstock` if stock is significantly above target coverage

Prioritization within the list:

- `priority_score = base(status) + stock_gap_component + reorder_component`
- where `base(critical) > base(warning) > base(ok)`
- the fewer `days_of_stock` and the higher the `reorder_qty`, the higher the ranking position

### `get_item_deep_dive`

Performs a deep analysis of a single SKU.

What it does:

- retrieves sales history for the product;
- analyzes the trend: growth, decline, stability, anomalies;
- evaluates current stock and reserves;
- considers the supplier, lead time, and minimum order quantity;
- calculates forecast and recommended order volume;
- generates a human-readable explanation of why the recommendation is what it is.

What it returns:

- sales history;
- trend;
- demand forecast;
- stockout risk;
- order recommendation;
- explanation in plain language.

Why it's needed:

When the agent finds a problematic SKU, it needs to not just flag it as a risk, but understand the specific cause and provide a meaningful recommendation.

Mathematical logic:

- `sales_7d = sum(quantity_sold over 7 days)`
- `sales_30d = sum(quantity_sold over 30 days)`
- `sales_90d = sum(quantity_sold over 90 days)`
- `avg_daily_sales_7d = sales_7d / 7`
- `avg_daily_sales_30d = sales_30d / 30`
- `avg_daily_sales_90d = sales_90d / 90`
- `trend_ratio = avg_daily_sales_7d / max(avg_daily_sales_30d, epsilon)`
- `forecast_7d = blended_velocity * 7`
- `forecast_14d = blended_velocity * 14`
- `forecast_30d = blended_velocity * 30`
- `blended_velocity = 0.6 * avg_daily_sales_7d + 0.4 * avg_daily_sales_30d`
- `target_stock = blended_velocity * (lead_time_days + safety_stock_days)`
- `raw_order_qty = max(0, target_stock - available_qty)`
- `recommended_order_qty = ceil(raw_order_qty / min_order_qty) * min_order_qty`
- then `recommended_order_qty` is capped via `max_stock_qty` if set

Trend interpretation:

- `trend_ratio > 1.15` — demand is accelerating
- `0.85 <= trend_ratio <= 1.15` — demand is stable
- `trend_ratio < 0.85` — demand is decelerating

### `build_purchase_order`

Generates a ready-made supplier order or a set of orders across multiple suppliers.

What it does:

- takes the list of products recommended for purchase;
- groups them by supplier;
- accounts for minimum order quantities;
- accounts for purchase prices;
- calculates the total order amount;
- prepares a purchase order structure ready for submission or confirmation.

What it returns:

- ready orders by supplier;
- list of items in each order;
- quantity per item;
- line totals and grand total;
- explanation of why each product was included in the order.

Why it's needed:

So the agent doesn't just advise on procurement, but turns the decision into an operational action that can be executed immediately.

Mathematical logic:

- the input is a list of SKUs with `recommended_order_qty`
- `supplier_group = group by supplier_id`
- `rounded_order_qty = ceil(recommended_order_qty / min_order_qty) * min_order_qty`
- `line_total = rounded_order_qty * purchase_price`
- `supplier_total = sum(line_total)`
- if a product is available from multiple suppliers, priority goes to `is_primary = true` unless there are special override rules

Result:

- one or more orders grouped by supplier
- each order line is based on deficit calculation, minimum order quantity, and purchase price

### `flag_dead_stock`

Finds products that are stagnant and require a separate decision.

What it does:

- looks for items with no sales or very weak movement;
- compares stock levels with the time since the last sale;
- evaluates how much the product is freezing working capital and warehouse space;
- generates recommendations for each case.

What it returns:

- list of dead stock or slow-moving products;
- problem priority;
- suggested action.

Typical recommendations:

- discount;
- promotion;
- bundle sale;
- return to supplier;
- downgrade purchase priority;
- full stop on reorder.

Why it's needed:

Not all warehouse problems are about stockouts. Sometimes the main problem is capital frozen in inventory that's no longer moving.

Mathematical logic:

- `dead_stock_days = today - last_sale_date`
- `stock_value = available_qty * purchase_price`
- `inventory_days = available_qty / max(avg_daily_sales_30d, epsilon)`

Rule-based logic for MVP:

- a product enters the dead stock list if `dead_stock_days` exceeds the threshold
- priority increases if both `available_qty` and `stock_value` are high
- recommendations depend on severity:
  - moderate case — discount
  - medium case — promotion / bundle
  - severe case — return to supplier / stop reorder

### `forecast_demand`

Builds a sales forecast for the next 7, 14, or 30 days.

What it does:

- analyzes sales history;
- identifies trends;
- accounts for seasonality;
- detects demand acceleration or deceleration;
- outputs expected sales volume for the selected horizon.

What it returns:

- 7-day forecast;
- 14-day forecast;
- 30-day forecast;
- confidence comment;
- factors that influenced the calculation.

Why it's needed:

Without a forecast, the agent could only rely on past stock levels. With a forecast, it can recommend purchases not by inertia, but based on expected demand behavior.

Mathematical logic:

- `sales_7d = sum(quantity_sold over 7 days)`
- `sales_30d = sum(quantity_sold over 30 days)`
- `avg_daily_sales_7d = sales_7d / 7`
- `avg_daily_sales_30d = sales_30d / 30`
- `blended_velocity = 0.6 * avg_daily_sales_7d + 0.4 * avg_daily_sales_30d`
- `forecast_N = blended_velocity * N`, where `N = 7 / 14 / 30`

Rationale for this MVP approach:

- the last 7 days provide sensitivity to recent demand changes
- the last 30 days provide stability and protect against random noise
- the final forecast is a compromise between the short-term signal and a more stable baseline

### `explain_decision`

Explains any agent decision in plain language.

What it does:

- takes an already-made agent decision;
- breaks it down into understandable reasons;
- removes technical noise and complex terms;
- translates calculations into human-readable wording.

What it returns:

- a short and clear explanation;
- key decision factors;
- reason for product selection;
- reason for volume selection.

Example of such an explanation:

`We recommend ordering this product now because it sells consistently, current stock will last less than a week, and delivery takes 10 days. If not ordered now, there's a high risk of going out of stock.`

Why it's needed:

The user needs to trust the agent. For this, the agent doesn't just act — it can explain its reasoning and make its conclusions transparent.

Mathematical logic:

- `explain_decision` itself doesn't generate forecasts; it uses results from other tools
- the input consists of already-calculated values:
  - `available_qty`
  - `velocity_7d`
  - `days_of_stock`
  - `lead_time_days`
  - `safety_stock_days`
  - `forecast`
  - `recommended_order_qty`
- then the agent converts these values into human-readable output

Conditionally:

- if `days_of_stock < lead_time_days`, the explanation emphasizes stockout risk
- if `trend_ratio > 1`, the explanation emphasizes demand acceleration
- if `recommended_order_qty = 0`, the explanation emphasizes that current stock is sufficient

## How the Agent Thinks

Below is the basic reasoning chain using the example question:

`What do I need to order this week?`

The agent acts sequentially:

1. calls `analyze_full_catalog`;
2. sees, for example, `12` red items and `23` yellow ones;
3. for each red item, calls `get_item_deep_dive`;
4. clarifies where the risk is real versus temporary noise;
5. forms the final purchase priority;
6. calls `build_purchase_order`;
7. groups products by supplier;
8. checks minimum order quantities and procurement economics;
9. delivers a specific action list to the user;
10. if needed, uses `explain_decision` to break down the recommendation in plain language.

## What It Looks Like for the User

The user sees not only the final answer but also the agent's work process.

Each tool call is displayed as a step in real time.

For example:

- the agent started analyzing the full catalog;
- the agent found critical SKUs;
- the agent opened a deep analysis for several products;
- the agent assembled a supplier order;
- the agent prepared a decision explanation.

This makes the process transparent:

- it's clear where the conclusion came from;
- it's clear which steps have already been completed;
- it's clear that the agent isn't giving a random answer but is actually going through a real decision-making workflow.

## Layer 4 — Interface

The product has two usage modes.

### 1. Dashboard

The dashboard is not the primary daily interface, but rather a visual picture of warehouse health.
This mode is for quick overview, product demos, team discussions, and understanding the overall temperature of the business.

It answers the question:

`What's currently happening with the warehouse and assortment?`

The dashboard shows:

- traffic light for all SKUs: red / yellow / green;
- top 10 most critical items;
- turnover chart;
- dead stock total value;
- forecast for the next 14 days.

Dashboard's role:

- quickly show the overall situation without diving into details;
- provide a visual picture for the owner or manager;
- help understand in a few seconds whether there are problems;
- serve as a showcase and demo layer for the product.

Important: the dashboard is not the primary working mode.
It's needed for overview and understanding, but doesn't replace operational work with the agent.

### 2. Chat with the Agent

Chat with the agent is the primary working mode of the product.

This is where the procurement manager, owner, or manager interacts with the system every day.
The user types in plain human language — no SQL, no filters, no manual report building.

Example queries:

- `What do I need to order this week?`
- `Which products are about to run out?`
- `What's stagnant in the warehouse?`
- `Build a supplier order for critical items.`
- `Why do you recommend ordering this particular product?`

In response, the agent provides not abstract analytics, but specific actions:

- which SKUs need attention;
- what exactly needs to be ordered;
- in what volume;
- from which supplier;
- which products should be liquidated;
- which decisions can be postponed;
- why the conclusion is what it is.

### Reasoning in the Interface

Inside the chat, the user sees reasoning not as hidden magic, but as an observable workflow.

That is, the interface shows:

- which tools the agent called;
- in what order it worked;
- what exactly it found at each step;
- how it went from intermediate findings to the final decision.

Example user experience:

- the agent ran `analyze_full_catalog`;
- the agent found critical SKUs;
- the agent called `get_item_deep_dive` for several items;
- the agent assembled `build_purchase_order`;
- the agent generated an explanation via `explain_decision`.

This makes the interface particularly strong for two reasons:

- the user sees that the decision is built on data and sequential logic;
- trust in the agent grows because the process is transparent, not hidden behind a single answer phrase.

### Role Separation Between Dashboard and Chat

These two modes have different purposes.

Dashboard:

- needed for overview;
- needed for visual understanding of the big picture;
- well suited for demos, monitoring, and quick scans.

Chat:

- needed for daily work;
- needed for decision-making;
- needed for giving the agent tasks in plain language;
- turns analytics into concrete action.

This is precisely why the product is built not around dashboard-first logic, but around agent-first logic:
the dashboard shows the state, while the chat helps take action.

## What's Stored in the Data

For this agent to work, the system already provides and uses the following core entities:

- suppliers;
- products;
- product-supplier relationships;
- warehouses;
- stock levels and reserves;
- sales history;
- supplier orders;
- order line items;
- analytical metrics;
- alerts;
- agent action log.

This data gives the agent a foundation for real decisions: from simple stock level monitoring to a full weekly replenishment workflow.

## Role of AI in the Product

AI here is not just for the chat interface.

Its purpose is to become the operational layer between raw data and business actions.
That means not just answering a question, but:

- understanding context;
- choosing the right tools;
- gathering data from multiple sources;
- making a decision;
- explaining the decision;
- initiating an action or alert.

This is precisely why `Stocky` is not just a dashboard and not just a forecasting model, but an agent that guides the user from signal to specific action.
