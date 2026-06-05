# Machines Domain

## Responsibility

This domain models the equipment being repaired. A machine can be known only partially at first and enriched later by dispatcher or technician input.

## First Use Cases

- Record brand and optional model from intake.
- Record machine location type.
- Link machine to request and customer.
- Store repair history once completed.

## Phase 02 Intake Ownership

Machine intake records can be partial at creation time. The machine domain owns the submitted brand, optional model, and location type (`home`, `office`, `coffee_shop`, `restaurant`, or `other`). Phase 02 links each intake machine to the submitted customer and the newly created service request.
