# External food databases: licensing and attribution

V1 ships only the `FoodSource` interface and a `MockFoodSource`. Before enabling a real
adapter, review the provider's current terms. The summary below was accurate when written;
always check the official pages.

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
