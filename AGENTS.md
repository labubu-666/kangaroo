# Layout
- `api` contains the FastAPI backend.
- `docs` contains the docs, they are served by the frontend but rendered on the backend at runtime.
- `web` contains the React frontend.
# Searching
- Use `rg` and `fzf` for search whenever possible.
# Styling
- Colours are semantic tokens defined in `web/src/index.css` (`surface`, `fg`, `border`, `primary`, `danger` and so on). Use them instead of `gray-*`, `white` or `blue-*` so dark mode works. Their values change under `.dark`.
- Status colours (green, yellow, purple, amber) are not tokens. Add a `dark:` variant next to them.
# Implementation
- Prefer simple solutions to complicated ones.
- Only do what was asked, dont wander off into tangents.
- Comments show explain `why` if you think the code needs explaining. Otherwise the code should describe itself.


