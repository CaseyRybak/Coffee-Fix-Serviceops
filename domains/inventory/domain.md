# Inventory Domain

## Responsibility

This domain tracks parts and consumables relevant to coffee machine repair.

## First Use Cases

- Store parts catalog.
- Store stock count.
- Link parts to brands and models.
- Reserve parts for a service request.

## Phase 07 Parts Suggestion Boundary

AI parts suggestions are inventory concepts only. They can name likely parts, explain compatibility assumptions, and help a dispatcher prepare, but they do not check live stock, create reservations, consume reservations, or modify a parts catalog.

Catalog and stock count arrive through the inventory workflow. Structured compatibility records and request-linked reservations were introduced by the Phase 16 inventory-reservations slice.

## Phase 08 Inventory Basics

Phase 08 adds a protected inventory workspace for staff with the `inventory` role. The inventory slice stores catalog parts, descriptive brand/model compatibility text, and current stock counts.

Technicians can mark parts used on assigned service requests. Parts usage decrements stock immediately and records the part usage against the request number. If stock is insufficient, usage is rejected and the service-request history is not changed.

This slice does not implement warehouses, purchase orders, suppliers, pricing, barcode scanning, billing totals, warranty claim stock handling, or AI-driven reservations.

## Phase 16 Inventory Reservations

Phase 16 adds operational reservations, stock movement history, structured part identity, and compatibility rows on top of the Phase 08 catalog and stock count.

Catalog identity rules:

- One factual physical part should map to one catalog SKU.
- Duplicate blocking uses a structured factual key made from part type, brand, key parameter label/value, and parameter unit.
- Fuzzy name matching is intentionally not used as a hard block, so genuinely different sizes or specs can coexist.
- Existing or previously existing factual parts should be reused instead of re-created under a new SKU.

Compatibility rules:

- Compatibility is stored separately from the part itself, so one part can apply to multiple exact models, model series, or generic machine groups.
- Inventory staff maintain catalog identity and compatibility metadata.
- Technicians reserve or consume parts during repair workflows; they do not own catalog deletion.

Reservation rules:

- Inventory staff can reserve parts for a service request, with an optional scheduled appointment reference.
- Active reservations reduce `available_quantity` but do not reduce `quantity_on_hand`.
- Reservation adjustment changes the active reserved quantity and records an audit movement.
- Reservation release restores available stock and records an audit movement.
- Technician parts usage consumes active reservations for the same request and part before consuming unreserved available stock.
- PostgreSQL reserve/release/consume paths lock the relevant stock and reservation rows before mutation so concurrent operators do not oversell available stock.

Stock visibility:

- Inventory part snapshots distinguish `quantity_on_hand`, `reserved_quantity`, and `available_quantity`.
- Low-stock checks use available quantity against an optional `low_stock_threshold`.
- Dispatchers can view a read-only low-stock list, but inventory create/update/reserve/release actions remain restricted to staff with the `inventory` role.

## Phase 21 Low-Stock Automation Boundary

Phase 21 allows n8n to send low-stock alerts from backend-owned owner dashboard data. The alert payload may include part id, SKU, part name, unit, available quantity, low-stock threshold, and an internal dashboard URL for staff follow-up.

n8n must not recalculate stock, reserve parts, adjust counts, create purchase requests, receive stock, change compatibility records, or expose stock movement notes beyond the intended staff alert. Procurement remains deferred to Phase 22.

## Phase 22 Procurement Lite

Phase 22 adds lightweight supplier and purchase-request workflows inside the inventory domain. Procurement is an internal staff workflow, not a public client feature and not an n8n-owned approval system.

Supplier rules:

- Inventory staff can create supplier records with contact fields and internal notes.
- Admin and inventory staff can read supplier and purchase-request records.
- Supplier records are intentionally simple: no billing, invoices, fiscal documents, payment terms, or vendor accounting.

Purchase request rules:

- Purchase requests move through `draft`, `pending_approval`, `approved`, `ordered`, `received`, and `cancelled`.
- Inventory staff create drafts, edit draft items, submit for approval, mark approved requests as ordered, receive ordered requests, and cancel requests before receipt.
- Admin staff approve pending purchase requests.
- The staff-facing procurement surface lives under `/inventory`; inventory staff see stock/procurement operations, while admin staff use the same workspace for procurement review and approval without inventory-only mutation controls.
- Draft items are tied to existing inventory parts and positive quantities.
- Low-stock draft creation uses backend-owned low-stock snapshots and creates a draft only for parts whose available quantity is at or below their threshold.

Receiving rules:

- Receiving is allowed only from `ordered`.
- Receiving increments `quantity_on_hand` for each purchase-request item.
- Each received item records a `procurement_receipt` stock movement with the resulting stock snapshot and a purchase-request reference in the movement note.
- Cancelled purchase requests do not change stock and received purchase requests cannot be cancelled.

Automation and AI boundary:

- n8n can alert staff about low stock but does not create, approve, order, receive, or cancel purchase requests.
- AI remains barred from autonomous procurement decisions. Later assistant work may propose drafts only through explicit human confirmation.

Still deferred:

- Multi-warehouse stock.
- Pricing, billing, warranty stock accounting, barcode scanning, and AI-created reservations.
- Full purchase orders, supplier billing, invoices, payments, warranty stock accounting, barcode scanning, and AI-created procurement.
