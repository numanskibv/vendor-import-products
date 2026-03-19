# Technische uitleg Vendor Import Module

Dit document is bedoeld voor ontwikkelaars/beheerders die willen begrijpen hoe de module intern werkt.

## 1. Architectuur

Belangrijkste onderdelen:

- **Wizardmodel**: `vendor.import.wizard` (TransientModel)
- **Categorie‑regels**: `vendor.category.rule`
- **Afbeeldingenwachtrij**: `vendor.import.image.queue`
- **Merken**: `product.brand`
- **Importprofielen**: `vendor.import.profile` en `vendor.import.profile.line` voor configureerbare kolommapping per leverancier/merk.
- **Configuratie**: uitbreiding op `res.config.settings` voor standaardmarge én de optie om alleen een hoofdafbeelding per producttemplate te gebruiken.

- **Help-popup**: `vendor.import.help` (TransientModel) met een HTML-handleiding en ChatGPT-prompt die als popup geopend kan worden vanuit het menu.

De module voegt daarnaast views en menu’s toe onder **Voorraad → Vendor Import** (Import leveranciers‑Excel, Categorie regels, Merken, Afbeeldingenwachtrij, Importprofielen, Handleiding &amp; prompt, Instellingen).

De kolommappings (`vendor.import.profile.line`) kunnen handmatig in de profiel‑formulieren worden beheerd of in bulk via de standaard Odoo‑import (Excel/CSV) op het model `vendor.import.profile.line`. Daarbij wordt meestal een hulpkolom `profile_id` gebruikt die via de importwizard op het veld **Profiel** (Many2one op naam) wordt gemapt.

## 2. Importflow (met importprofielen en TGH‑fallback)

1. **_parse_tgh_excel()**
   - Controleert dat er een bestand en leverancier gekozen zijn.
   - Valideert de bestandsnaam tegen de leveranciersreferentie (prefix, bv. `TGH`).
   - Opent het Excelbestand via `openpyxl`.
   - Normaliseert kolomnamen (lowercase, spaties en speciale tekens verwijderd).
   - Probeert eerst een **importprofiel** (`vendor.import.profile`) te vinden dat past bij leverancier, bestandsnaamprefix en kolomtitels. Dit gebeurt via een classmethode zoals `vendor.import.profile.match_profile(...)`, die:
     - alle actieve profielen voor de leverancier met passende bestandsnaamprefix ophaalt;
     - per profiel controleert of de in het profiel gedefinieerde kolompatronen (rollen) in de Excel‑headers voorkomen;
     - een mapping `rol → kolomindex` en een lijst met image‑kolomindices teruggeeft.
   - Als er een profielmatch is:
     - worden kolommen voor o.a. productnaam, merk, kleur, maat, barcode, inkoopprijs, categorie en afbeeldingen bepaald door het profiel in plaats van door hardcoded kolomnamen;
     - kunnen verschillende layouts per leverancier/merk met dezelfde code worden ingelezen.
   - Als er geen profiel beschikbaar is of niets matcht:
     - valt de code terug op de bestaande TGH‑fingerprint en hardcoded kolomnamen (de oorspronkelijke TGH‑import blijft dus werken als fallback).
   - Bouwt vervolgens een datastructuur met per template:
     - `rows`: rijen met kleur/maat/sku/barcode/prijzen/variant‑image‑urls.
     - `colors`, `sizes`, `sale_prices`.
     - `image_urls` op template‑niveau.
   - Retourneert `(products_data, meta, parse_errors, parse_warnings)`.

2. **action_test_tgh()**
   - Roept `_parse_tgh_excel()` aan.
   - Voert alle checks uit, maar schrijft niets weg naar de database.
   - Slaat een HTML‑rapport op in `test_report_html`.

3. **action_import_tgh()**
   - Draait `_parse_tgh_excel()` opnieuw (failsafe bij gewijzigde bestanden).
   - Doorloopt elk "bucket" (template) en:
     - Maakt/zoekt `product.template`.
     - Zorgt dat attributen `Kleur` en `Maat` bestaan.
     - Maakt variantcombinaties aan.
     - Schrijft prijzen, SKU, barcodes.
     - Koppelt leverancier via `product.supplierinfo`.
     - Past categorie‑regels toe (indien aangevinkt).
     - Creëert categorieën vanuit Excel (indien aangevinkt).
     - Koppelt merk.
     - Plant afbeeldingen in de image queue.

### 2.1 Voorbeeld van een importprofiel

Een `vendor.import.profile` bestaat uit een header (naam, leverancier, optioneel bestandsnaamprefix) en één of meer `vendor.import.profile.line` records die een rol koppelen aan een kolomtitel.

Voorbeeldprofiel voor leverancier **TGH**:

- Profiel:
  - Naam: "TGH standaardlayout"
  - Leverancier: TGH
  - Bestandsnaamprefix: `TGH_`

- Profielregels (vereenvoudigd):
  - Rol `product_name` → headerpatroon: `produktname`
  - Rol `brand` → headerpatroon: `marke`
  - Rol `barcode` → headerpatroon: `gtin`
  - Rol `color` → headerpatroon: `farbe`
  - Rol `size` → headerpatroon: `größe`
  - Rol `purchase_price` → headerpatroon: `ek-preis`
  - Rol `image_main` → headerpatroon: `link für produktbild`

Als een Excelbestand met naam `TGH_...xlsx` deze kolomtitels (of varianten daarvan) bevat, zal `match_profile()` dit profiel kiezen en de parser vertellen in welke kolommen productnaam, merk, barcode, kleur, maat, inkoopprijs en hoofdafbeelding staan.

Voor een andere leverancier of merk kun je een tweede profiel aanmaken met andere headerpatronen (bijvoorbeeld Nederlandse kolomnamen als `Artikelnaam`, `Merknaam`, `EAN code`, `Kleur`, `Maat`, `Productimage url basis`, enz.). De wizard hoeft daarvoor niet aangepast te worden; alleen de profielen bepalen hoe de kolommen gelezen worden.

## 3. Categorie‑regels

Model: `vendor.category.rule`.

- Belangrijke velden:
  - `vendor_code` – code van de leverancier (`tgh`, `any`, ...).
  - `keyword` / patroon – zoekwoord in productnaam.
  - `match_type` – bijvoorbeeld "contains" (deelstring).
  - `category_id` – doelproductcategorie.
  - `priority` – hogere waarde wint bij meerdere matches.
  - `active` – alleen actieve regels worden gebruikt.
  - `audience` – doelgroep (bijv. Heren, Dames, Kids, Unisex of Alle doelgroepen).
- De methode `match(name, vendor_code)` vindt de beste regel voor een productnaam.

Technisch detail:

- Er is een SQL‑constraint op `(vendor_code, keyword, category_id, audience)` zodat je voor hetzelfde zoekwoord/categorie meerdere regels met verschillende doelgroepen kunt hebben, maar niet exact dubbele regels.

In `action_import_tgh()`:

- Als `apply_category_rules` aan staat, wordt na het aanmaken/zoeken van een template:
  - `rule = CategoryRule.match(product_name, vendor_code)` aangeroepen.
  - Alleen als er nog geen categorie is of de template net nieuw is, overschrijft de regel de categorie.

## 4. Analyse‑modus en conceptregels

In `vendor.import.wizard`:

- **_collect_category_analysis()**
  - Gebruikt `_parse_tgh_excel()` om unieke productnamen te verzamelen.
  - Bepaalt per naam of er een `vendor.category.rule`‑match is.
  - Bouwt statistieken en suggesties voor nieuwe zoekwoorden.

- **action_analyse_import_file()**
  - Roept `_collect_category_analysis()` aan.
  - Schrijft een tekstueel rapport in `analysis_log`.

- **action_create_draft_rules()**
  - Gebruikt dezelfde analyse‑output.
  - Maakt `vendor.category.rule` records aan voor gemiste namen:
    - Naam: `AUTO: <keyword>`.
    - Vendor code: `draft_vendor_code`.
    - Match‑type: `contains`.
    - Categorie: placeholder **Te categoriseren** onder **Bedrijfskleding**.
    - Prioriteit: `draft_priority_base + offset`.
    - Active: volgens `draft_active`.

## 5. Image queue

Model: `vendor.import.image.queue`.

- Unieke index op `(vendor_id, product_tmpl_id, COALESCE(product_id, 0), url)` voorkomt dubbele jobs.
- Jobs worden aangemaakt in de importwizard:
  - Template‑niveau: alle unieke `image_urls` per template.
    - Als de config‑parameter `vendor_import_module.template_image_only` (instelling **Alleen hoofdafbeelding per product (geen variantfoto's)**) AAN staat, wordt per template slechts één URL behouden (de eerste gesorteerde) om schijfruimte te besparen.
  - Variant‑niveau (standaard): alleen URLs die niet al bij de template staan (om dubbele jobs te voorkomen wanneer varianten dezelfde foto delen).
    - Als `template_image_only` AAN staat, worden variant‑specifieke URLs volledig overgeslagen; alle varianten gebruiken dan de templatefoto.

Verwerking:

- Cron en `action_process_images_now` roepen `_process_pending_jobs()` aan.
- Per batch:
  - Download via `_download_image_b64()` met caching per URL.
  - Past de afbeelding toe via `_apply_image()`:
    - Zet `image_1920` op template en/of variant (als nog leeg).
    - Maakt optioneel `product.image` records aan.
  - Update `state`, `attempts`, `last_error`, `done_date`.

## 6. Reset image queue

- `action_reset_image_queue()` op de wizard:
  - Verwijdert alle jobs in `vendor.import.image.queue` voor de gekozen leverancier.
  - Stuurt een `display_notification` naar de gebruiker.
  - Roept `_compute_image_queue_counts()` opnieuw aan zodat de UI‑tellers direct kloppen.

- `action_reset_vendor_queue()` op `vendor.import.image.queue`:
  - Wordt aangeroepen via de knop **Reset queue voor leverancier** op het formulier van een queue‑record.
  - Verwijdert eveneens alle jobs voor de betreffende leverancier en toont een notificatie.
  - Maakt het mogelijk om vanuit het Afbeeldingenwachtrij‑overzicht de volledige queue voor een leverancier leeg te trekken.

## 7. Vertalingen

- De module bevat Nederlandse vertalingen in `i18n/nl.po` en/of `i18n/nl_NL.po`.
- Nieuwe/gewijzigde fout‑ en uitlegberichten in Python of XML moeten via de standaard Odoo i18n‑export worden opgenomen en vertaald.

Deze uitleg is bedoeld als uitgangspunt voor verdere ontwikkeling of debugging. Voor dagelijkse gebruikers is `handleiding.md` de aangewezen referentie.
