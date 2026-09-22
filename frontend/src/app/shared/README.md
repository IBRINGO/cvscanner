# shared/

Reusable, feature-agnostic building blocks. Nothing in `shared/` may import
from `features/` or contain business logic tied to a specific feature.

- `components/ui`, `components/buttons`, `components/dialogs`,
  `components/cards`, `components/tables`, `components/badges`,
  `components/progress`, `components/charts` — presentational components,
  added as real screens need them. Phase 1 only adds
  `components/ui/placeholder-page`, used by feature routes that are not
  built yet.
- `directives/`, `pipes/`, `validators/` — small, pure, reusable Angular
  primitives.
- `models/` — cross-feature TypeScript types (e.g. pagination envelopes).
- `utils/` — framework-free helper functions.
