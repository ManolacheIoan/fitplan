# External food data: licensing and attribution

FitPlan ships an **Open Food Facts** (OFF) adapter (`open_food_facts.py`, enabled with
`FOOD_SOURCE=open_food_facts`) and a `MockFoodSource` for tests.

> **Not legal advice.** This summary is based on the text of the Open Database License
> 1.0 (sections quoted below) and OFF's API documentation, read in October 2026. Have it
> reviewed by a lawyer before going public, and re-check the official pages:
> <https://opendatacommons.org/licenses/odbl/1-0/>, <https://world.openfoodfacts.org/terms-of-use>.

## Licences that apply to OFF data

| Part | Licence |
|---|---|
| The database | Open Database License (ODbL) 1.0 |
| Individual contents (each product's values) | Database Contents License (DbCL) |
| Product images | CC BY-SA (FitPlan does not use images) |

OFF data is contributed by volunteers and comes with no guarantee of accuracy.

## What the ODbL requires, applied to FitPlan

**Attribution on what users see (ODbL 4.3, "Produced Work").** Showing OFF values in the
app is a *Produced Work*. When a Produced Work is used publicly, the licence requires "a
notice associated with the Produced Work" that tells people the content was obtained from
the database and is available under the ODbL.
FitPlan shows "Sursa: Open Food Facts, date disponibile sub licența ODbL" (both linked) on
external search results, on the add form and on logged entries that use OFF data
(`frontend/src/features/logs/Attribution.tsx`).

**Saving products locally creates a Derivative Database (ODbL 1.0, 4.4 and 4.6).**
FitPlan copies the products found into its own `foods` table. It also changes them: values
are rounded to 0.1, the brand is appended to the name, and incomplete or implausible
products are dropped. Under the ODbL, a "modification" of the database, or extracting a
substantial part of it into a new database, is a **Derivative Database**. A database
built from repeated searches can grow into a substantial part over time.

What follows from that:
- **Share-alike (4.4).** A Derivative Database that is "Publicly Used" must be licensed
  under the ODbL. Only the OFF-derived rows are concerned, not FitPlan's own data (demo
  foods, users' private foods, logs). Those rows are identifiable by
  `external_source = 'open_food_facts'`.
- **Access (4.6).** If FitPlan publicly uses a Derivative Database, or a Produced Work from
  it (the app showing those values to users), it "must also offer" recipients either a
  machine-readable copy of the Derivative Database, or a file describing the changes made
  or the method of making them.
  FitPlan's method is deterministic and documented in `parse_hit()` (round to 0.1, name
  plus first brand, skip hits with missing values, kcal outside 0–900 or macros above
  100 g). Publishing that description, or an export of the OFF-derived rows, is the
  likely way to comply; the lawyer should confirm which.
- **Internal use only (4.5c).** Use "internally within an organisation" is not public use.
  A public app is not internal use.
- **Notices (4.2).** If the OFF-derived rows are ever distributed (for example a database
  dump, a public repository containing the data, or a bulk export), include the ODbL
  licence or its URI and keep existing notices.

**Other consequences of caching.**
- Cached products do not follow later corrections or deletions on OFF. Values can be
  outdated; the UI asks users to check the label.
- Cached rows never contain user data. Who searched for what is not stored, apart from the
  search text, which is kept up to 24 h in server memory and not linked to any account.

## How FitPlan respects OFF's API rules

- Search runs only when the user presses "Caută în Open Food Facts". OFF's documentation
  asks not to use the API for search-as-you-type. Local search stays instant.
- OFF allows about 10 search requests per minute per IP. FitPlan allows at most 8 per
  minute for the whole app and 4 per minute per user, and does not resend the same term
  for 24 h.
- Requests carry an identifying User-Agent (`OFF_USER_AGENT`, "App/Version (contact)").
- The privacy policy (version 2026-10-v3) says what is sent (only the search text, from
  the server) and to whom.

## Before going public: your checklist

1. Set `OFF_USER_AGENT` on Render to `FitPlan/<version> (<your contact email>)`.
2. Fill in OFF's short API usage form, linked from their API documentation, and read
   their terms of use.
3. Have the ODbL obligations reviewed, in particular how to meet section 4.6:
   - publish the description of the alteration method; or
   - offer an export of the OFF-derived rows under the ODbL.

   Then add a link to it from the app (for example from the attribution line or the
   privacy page).
4. Never publish or ship the `foods` table, or a dump containing OFF rows, without the
   ODbL licence notice.
5. Keep the attribution visible wherever OFF values appear. It is already in place; keep
   it when redesigning screens.
6. Complete the operator and contact placeholders in the privacy policy, and check the
   processing agreements with the hosting providers.
