# External food databases: licensing and attribution

FitPlan ships an **Open Food Facts** adapter (`open_food_facts.py`, enabled with
`FOOD_SOURCE=open_food_facts`) and a `MockFoodSource` for tests. The summary below was
accurate when written (October 2026); always check the official pages.

## How FitPlan complies with Open Food Facts' rules
- Search runs only when the user presses "Caută în Open Food Facts" (their docs ask not to
  use the API for search-as-you-type). Local search stays instant.
- Their limit is about 10 searches/min per IP. FitPlan allows at most 8/min for the whole
  app and 4/min per user, and does not resend the same term for 24 h.
- Requests carry an identifying User-Agent (`OFF_USER_AGENT`, "App/Version (contact)").
- Results are cached in `foods` (`source = external`, `external_source = open_food_facts`);
  hits with missing or implausible values are skipped.
- Attribution ("Open Food Facts (ODbL)", linked) is shown with search results, on the add
  form and on logged entries that use their data.
- The privacy policy (version 2026-10-v2) states that only the search text is sent.
- OFF asks API users to describe their use in a short form; do this before going public.

## USDA FoodData Central (FDC)
- Data is published by the U.S. Department of Agriculture and is in the **public domain**
  (CC0 1.0). Attribution is not legally required but USDA asks that it be cited, e.g.
  "U.S. Department of Agriculture, Agricultural Research Service. FoodData Central."
- The API requires a free **api.data.gov key**, which has rate limits. Keep the key in an
  environment variable, never in the repository.
- Names are in English; a Romanian UI will need translation or bilingual search.

## Open Food Facts (OFF)
- The database is licensed under the **Open Database License (ODbL)**; individual
  contents under the Database Contents License; product images under CC BY-SA.
- **Attribution is required** (e.g. "Date: Open Food Facts, openfoodfacts.org, ODbL")
  visible where the data is shown.
- **Share-alike**: if you publicly distribute a database derived from OFF (our `foods`
  cache with OFF rows counts), it must also be made available under the ODbL.
- Identify your app with a custom User-Agent and respect the API rate limits.
- Data is crowd-sourced: values may be missing or wrong; validate before caching.

## Implementation checklist
1. Add an adapter class implementing `FoodSource` in this package.
2. Register it in `get_food_source()` and set `FOOD_SOURCE=<name>`.
3. Show the required attribution in the UI for foods whose `source` is `external`.
4. Update the privacy policy if search terms are sent to the provider.
