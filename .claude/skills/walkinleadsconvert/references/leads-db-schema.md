# Interview Datenbank (Leads DB) — schema snapshot

Snapshot taken 2026-06-29 from the live data source. Use this so each run is deterministic and
you don't re-fetch the 84k-char DB dump. If a write fails because an option/property name changed,
re-fetch the data source (`collection://31cbebb0-c2f9-8075-b996-000b1747664a`) and update this file.

## Notion IDs (single source of truth)

- **Operations Cockpit** page: `311bebb0c2f980de89a0f3d463a0fbce`
- **💡 walk-in callout** lives on that page (gray callout). Block: `389bebb0c2f9804eb2bef28e599c0a68`
- **Interview Datenbank** (Leads DB) database: `31cbebb0c2f980479e9ffc59851f8a34`
  - data source: `collection://31cbebb0-c2f9-8075-b996-000b1747664a`
  - default page template (Discovery Interview body): `31cbebb0c2f980acb238caced7a687f1`
- **Hot Leads callout** = inline linked **"View of Interview Datenbank"**, block `388bebb0c2f980139071ce86f2d65923`
  - filter (after one-time widening): `HOT STATUS` is any of `HOT` / `QUITE HOT` / `WALK IN BUT NO BAMFAM`

## Property map for a walk-in conversion

Set exactly these on each converted lead. Property names are **case-sensitive** and must match verbatim.

| Property | Type | Value to set | Source |
|---|---|---|---|
| `Name` | title | company name, mirror existing `"{Firma} {City}"` style (e.g. "Sereo Baden"); just Firma if no city | callout + web |
| `Firma` | text | company name | callout |
| `Geschäftsführer / CEO` | text | contact person, if named | callout |
| `Rolle` | select | closest option (see below), if a role was mentioned | callout |
| `email` | text | contact email (lowercase property name!) | callout / web |
| `website` | url | official site | callout / web |
| `phone` | text | if found | callout / web |
| `city` | text | town | callout / web |
| `postalCode` | text | if found | web |
| `Branche` | select | **best match from the existing options below — never create a new one** | web |
| `Größe` | select | `Solo (1 Person)` / `2–5 Mitarbeiter` / `6–10 Mitarbeiter` / `10+` | web |
| `Context` | text | 5-line call card (format below) | web |
| `Outreach Channel` | select | `Walk-In` | fixed |
| `Outreach Gemacht?` | checkbox | ✓ (true) | fixed |
| `Contacted` | checkbox | ✓ (true) | fixed |
| `Gesprächsdatum` | date | the walk-in date = the `✅ {date}` on the line | callout |
| `Last contacted` | date | same walk-in date | callout |
| `Pipeline Stage` | status | `Problem Interview` | fixed |
| `HOT STATUS` | select | `WALK IN BUT NO BAMFAM` | fixed |
| `War-Room Status` | select | `○ Offen – keine Antwort` (only if currently blank) | fixed |

`Context` 5-line format (same as the daily enrichment workflow — grounded, never invented):

```
WAS: <what the company does, 1 line>
GROESSE: <employee/size signal>
STANDORT: <city / region>
AUFHAENGER: <concrete hook for the conversation>
OPENER: <one German opening line we could use>
```

## Exact select options (match verbatim)

- **`HOT STATUS`**: `HOT` · `?` · `2 Weeks` · `QUITE HOT` · `WALK IN BUT NO BAMFAM`
- **`War-Room Status`**: `○ Offen – keine Antwort` · `◑ Reagiert – Termin fixieren` · `● BAMFAM – Termin gebucht` · `✓ Interview erledigt` · `✕ Tot / Disqualifiziert`
  - (these contain en-dashes `–` on purpose — they are fixed enum values, copy them exactly)
- **`Outreach Channel`**: `Walk-In` · `Cold Call` · `WhatsApp` · `E-Mail` · `AI Cold Call`
- **`Rolle`**: `Founder / Inhaber` · `Admin / Office` · `Operations` · `Freelancer` · `Mitarbeiter` · `Leiter/Chef Stv.`
- **`Größe`**: `Solo (1 Person)` · `2–5 Mitarbeiter` · `6–10 Mitarbeiter` · `10+`
- **`Pipeline Stage`** (status): `Problem Interview` (default starting stage)
- **`Enrichment Status`**: `Angereichert` · `Website zu dünn` · `Kein Website`

### `Branche` — pick the closest existing option (153 of them; do NOT add new ones)

Fitness / Personal Trainer · Physiotherapie / Gesundheit · Beauty / Barber · Kreativ (Foto / Video / Design) · Marketing / Agentur · Coaching / Beratung · Handwerk · E-Commerce · Gastronomie · Immobilien · Automobil · Treuhand · Getränke · Rechtsbranche · Modebranche · Bücher · Einzelhandel · Sport und Spass · Medizin · Personalvermittlung · Architektur · Finanz · Landwirtschaft · Hauswirtschaft · Reinigung · Unbekannt · IT & Software · Unternehmensberatung · Beratung · Marketing & Werbung · Finanzdienstleistungen · Gesundheitswesen · Steuerberatung · Ingenieurwesen · Öffentliche Verwaltung · Industrieautomation · Personalberatung · Rechtsberatung · Design & Architektur · Ingenieurdienstleistungen · Bauwesen · Tourismusberatung · Immobilienverwaltung · Medizintechnik · Werbetechnik · Personalvermittlung & Interim Management · Personaldienstleistungen · Versicherungsmakler · Versicherungswesen · Handel · Schmuckherstellung · Versicherungen · Büroservice · Buchhaltung & Steuerberatung · Versicherungsdienstleistungen · Facility Management · Landwirtschaft & Weinbau · Elektronikfertigung · Logistik & Umzugsdienstleistungen · Dekoration & Werbung · Lektorat & Textdienstleistungen · Rechtswesen · Gartenbau · Öffentliche Sicherheit · Automobilhandel · Immobilien & Architektur · Hausmeisterservice · Versicherungsvermittlung · Verpackungsindustrie · Treuhanddienstleistungen · Treuhand & Immobilien · Gebäudereinigung · HR-Beratung · Industrie & Handwerk · Gebäudemanagement · Marketing & IT-Dienstleistungen · Telekommunikation · Bildungswesen · Automobilservice · Fahrzeugreparatur · Elektronik · Design & Kreativdienstleistungen · Elektroinstallation · IT & Unternehmensberatung · Berufsberatung · Wirtschaftsprüfung · Grafikdesign · Druckerei & Werbedienstleistungen · Webdesign & Marketing · Coaching & Beratung · Versicherungsberatung · Architektur & Innenausbau · Immobilien & Treuhand · Weinbau · Elektrotechnik · Freizeit & Erholung · Automobilbranche · Transport & Logistik · Reinigungsdienstleistungen · Haushaltsgeräteservice · Energieversorgung · Videoproduktion & Fotografie · Immobilienentwicklung · Treuhandwesen · Immobilienberatung · Fotografie & Videografie · Bildung & Unterkunft · Life Sciences · Beratung & Management · Friseurwesen · Kosmetik & Schönheitspflege · Friseurhandwerk · Friseurbranche · Kosmetik & Friseurdienstleistungen · Kosmetik & Körperpflege · Kosmetik & Friseur · Friseurdienstleistungen · Friseursalon · Schönheitsdienstleistungen · Kosmetik & Friseurwesen · Friseur & Barbier · Friseursalon & Kosmetik · Friseursalon & Kosmetikstudio · Tierpflege · Friseur & Schönheitspflege · Einzelhandel & Tankstellen · Gastgewerbe · Erwachsenenunterhaltung · Architektur & Bauwesen · Bürodienstleistungen · Garten- und Landschaftspflege · Gastronomie & Friseurwesen · Fitness & Wellness · Fitness & Sport · Tanzschule · Sport & Freizeit · Gartenpflege · Architektur & Design · Gebäudetechnik · Innenarchitektur · Smart Home & Gebäudeautomation · Messtechnik · Sicherheitsdienstleistungen · Fitnessstudio · Coaching & Fitness · Hotel & Wellness · Hotellerie · Fitness & Gesundheit · Sport & Fitness · Fitnessbranche · Fitness & Coaching · Friseurgewerbe · Safebau

If nothing fits, use `Unbekannt` (don't invent a new option — the select is already bloated).

## Dedup (cross-check) — how

SQL `query-data-sources` is **plan-gated** (returns 400 "Business plan required"), so dedup goes through
search, not SQL:

1. `notion-search` with `data_source_url: collection://31cbebb0-c2f9-8075-b996-000b1747664a` and the
   company name as the query.
2. `notion-fetch` the top 1–2 hits and confirm it's the same company by `Firma` / website domain / email
   (not just a fuzzy title match — "M & P Treuhand" ≠ "MP Immobilien").
3. Match → **expand** that page. No confident match → **create** a new lead.

## Merge rules on expand (don't clobber)

- Fill a property **only if it's currently empty**. Never overwrite data the operator/enrichment set.
- **Always** set `HOT STATUS = WALK IN BUT NO BAMFAM` — **except** if it's already `HOT` or `QUITE HOT`
  (those are hotter; keep them and note it in the report).
- Set `War-Room Status` / `Outreach Channel` only if blank.
- Append the raw walk-in note as a new block; never replace the existing page body.
