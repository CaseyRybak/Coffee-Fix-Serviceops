# Inventory Domain

## Responsibility

This domain tracks parts and consumables relevant to coffee machine repair.

## First Use Cases

- Store parts catalog.
- Store stock count.
- Link parts to brands and models.
- Reserve parts for a service request.

## Phase 07 Parts Suggestion Boundary

AI parts suggestions are inventory concepts only. They can name likely parts, explain compatibility assumptions, and help a dispatcher prepare, but they do not check live stock, create reservations, or modify a parts catalog.

Catalog, stock count, compatibility records, and reservations remain Phase 08 scope.

## Phase 08 Inventory Basics

Phase 08 adds a protected inventory workspace for staff with the `inventory` role. The inventory slice stores catalog parts, descriptive brand/model compatibility text, and current stock counts.

Technicians can mark parts used on assigned service requests. Parts usage decrements stock immediately and records the part usage against the request number. If stock is insufficient, usage is rejected and the service-request history is not changed.

This slice does not implement warehouses, purchase orders, suppliers, pricing, barcode scanning, billing totals, warranty claim stock handling, or AI-driven reservations.
