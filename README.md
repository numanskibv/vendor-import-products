# Vendor Import Module (Odoo 18)

Een Odoo 18-module om leveranciers‑Excelbestanden veilig en herhaalbaar te importeren. De module biedt een wizard met testmodus, analyse‑modus voor categorie‑regels, een wachtrij voor productafbeeldingen en configureerbare importprofielen per leverancier/merk.

## Belangrijkste functies

- **Importwizard voor leveranciers‑Excel** met validaties op leverancier en bestandsnaam.
- **Testmodus** die het Excelbestand volledig doorloopt zonder data te wijzigen.
- **Analyse‑tab** die laat zien welke productnamen afgedekt zijn door categorie‑regels en conceptregels kan aanmaken.
- **Categorie‑regels (vendor.category.rule)** om productcategorieën automatisch te bepalen op basis van zoekwoorden.
- **Ondersteuning voor merken (product.brand)** en optionele categoriekolom uit Excel.
- **Afbeeldingenwachtrij (vendor.import.image.queue)** met cron‑job, handmatige knoppen voor verwerken en resetten, én een eigen overzichtsscherm met filters.
- **Standaardmarge instelbaar** via Instellingen → Vendor Import.
- **Optie om alleen een hoofdafbeelding per producttemplate op te slaan** (en dus géén variantfoto's per maat/kleur) om schijfruimte te besparen.
\- **Importprofielen (vendor.import.profile)** om per leverancier/merk verschillende Excel‑kolomindelingen te ondersteunen zonder extra code, inclusief Excel‑import van kolommappings.

## Vereisten

- Odoo 18 (community of enterprise).
- Afhankelijkheden: `stock`, `product`, `purchase`, `website_sale`.
- Python‑package `openpyxl` moet geïnstalleerd zijn in de Odoo‑omgeving.

## Installatie

1. Plaats de map `vendor_import_module` in een addons‑pad (zie `addons_path` in odoo.conf).
2. Herstart de Odoo‑server.
3. Ga naar **Apps**, update de app‑lijst, zoek op "Vendor Import Module" en installeer.
4. Controleer dat in **Voorraad** een nieuw hoofdmenu **Vendor Import** verschijnt met o.a.:
   - **Import leveranciers‑Excel** (wizard)
   - **Categorie regels**
   - **Merken**
   - **Afbeeldingenwachtrij**
   - **Importprofielen**
   - **Handleiding &amp; prompt** (in-app uitleg en ChatGPT-prompt)
   - **Instellingen** (configuratiescherm)

## Configuratie

1. **Standaardmarge**
   - Ga naar **Configuratie → Vendor Import → Instellingen**.
   - Stel het veld **Standaard marge (%)** in.

2. **Afbeeldingsstrategie (alleen hoofdafbeelding)**
   - In hetzelfde scherm kun je de optie **Alleen hoofdafbeelding per product (geen variantfoto's)** aanzetten.
   - Als deze optie **aan** staat:
     - Wordt per producttemplate nog maar één afbeelding‑URL ingepland (de eerste),
     - worden variant‑specifieke afbeeldingen per maat/kleur overgeslagen,
     - en blijft de totale image queue én opslag kleiner.

3. **Importprofielen (kolommapping per leverancier/merk)**
   - Ga naar **Voorraad → Vendor Import → Importprofielen**.
   - Maak per leverancier/merk een profiel aan met een duidelijke naam en eventueel een bestandsnaamprefix.
   - Voeg in het tabblad voor kolommapping regels toe die aangeven welke Excel‑kolomtitel welke rol heeft (bijv. productnaam, merk, barcode, maat, kleur, inkoopprijs, hoofdafbeelding, extra afbeelding).
   - Bij het testen/importeren probeert de wizard eerst een passend profiel te vinden; alleen als er geen match is, valt hij terug op de hardcoded TGH‑layout.

4. **Leveranciershandleiding**
   - Open de TGH‑leverancier bij **Contacten**.
   - Vul in het tabblad Vendor Import de **handleiding voor Excel‑kolommen** in (HTML‑tekst).
   - Deze handleiding wordt getoond in de wizard.

5. **Categorie‑regels**
   - Ga naar **Voorraad → Vendor Import → Categorie regels**.
   - Maak regels per combinatie van:
     - Leveranciercode (bv. `tgh` of `any`)
     - Zoekwoord/patroon in de productnaam
     - Doelcategorie
   - Gebruik de Analyse‑modus in de wizard om conceptregels (`AUTO:`) te laten genereren en daarna te verfijnen.

6. **Cron voor afbeeldingen**
   - In **Instellingen → Technisch → Geplande acties** is een taak aanwezig om de image queue periodiek te verwerken (model `vendor.import.image.queue`, methode `_cron_process_queue`).

## Gebruik (korte versie)

1. Ga naar **Voorraad → Vendor Import → Import leveranciers‑Excel**.
2. Kies leverancier **TGH** en upload het Excelbestand.
3. Stel marge, publicatie en overige opties in.
4. Klik **Test**:
   - De wizard draait alle checks en toont een HTML‑rapport.
   - Producten/varianten worden nog **niet** aangemaakt of gewijzigd.
5. Controleer het rapport en pas Excel of categorie‑regels aan indien nodig.
6. (Optioneel) Ga naar de tab **Analyse** en draai **Analyse** om te zien welke namen geen categorie‑match hebben.
7. (Optioneel) Maak vanuit Analyse **conceptregels** aan en verfijn deze in **Categorie regels**.
8. Als de test goed is, klik **Importeer** om producten, varianten, categorieën, merken en leveranciersinfo bij te werken.
9. Afbeeldingen:
   - De import vult de **image queue** met downloadjobs.
   - Gebruik de knop **Process images now** in de wizard of wacht op de cron.
   - Met **Reset image queue** kun je alle openstaande jobs voor deze leverancier wissen.

## Analyse‑modus en conceptregels

De Analyse‑tab in de wizard:

- Parseert hetzelfde Excelbestand als de test/import.
- Groepeert op unieke productnamen.
- Matcht elke naam tegen `vendor.category.rule` op basis van leveranciercode.
- Toont in het rapport hoeveel templates wél/niet gematcht zijn.
- Kan, indien gewenst, **conceptregels** (`AUTO:`) aanmaken voor namen zonder match.

Conceptregels:

- Worden aangemaakt in model `vendor.category.rule`.
- Krijgen als categorie standaard een placeholder **Te categoriseren** onder de productcategorie **Bedrijfskleding**.
- Worden standaard **inactief** aangemaakt zodat je ze eerst kunt controleren.
- Kun je achteraf per regel aanpassen (categorie, doelgroep, prioriteit) en activeren.

## Image queue

- Elke unieke afbeelding‑URL in de Excel wordt in `vendor.import.image.queue` gezet als job.
- Template‑niveau foto’s worden één keer in de queue gezet; gedeelde foto’s voor varianten worden niet opnieuw ingepland.
- Variant‑specifieke foto’s (andere URL dan de template) krijgen wel een eigen job.
- De cron of de knop **Process images now** downloadt afbeeldingen, zet `image_1920` en maakt optioneel extra `product.image` records aan.
- Met **Reset image queue** in de wizard verwijder je alle jobs voor de geselecteerde leverancier en worden de tellers in de wizard direct ververst.
- Via **Voorraad → Vendor Import → Afbeeldingenwachtrij** heb je een apart overzichtsscherm met filters op leverancier/status en een knop **Reset queue voor leverancier** op het formulier van een taak om de volledige queue voor die leverancier vanuit daar leeg te maken.

## Ontwikkelaarsnotities

- Hoofdmodel wizard: `vendor.import.wizard` (TransientModel).
- Belangrijke modellen:
  - `vendor.category.rule` – categorie‑regels per leveranciercode en zoekwoord.
  - `vendor.import.image.queue` – wachtrij voor afbeeldingsdownloads.
  - `product.brand` – merken gekoppeld tijdens import.
- Belangrijke acties in de wizard:
  - `action_test_tgh` – testmodus.
  - `action_import_tgh` – daadwerkelijke import.
  - `action_analyse_import_file` – analyse‑modus.
  - `action_create_draft_rules` – conceptregels aanmaken.
  - `action_process_images_now` – image queue direct verwerken.
  - `action_reset_image_queue` – image queue leegmaken voor leverancier.

Meer details vind je in de bestanden `handleiding.md` (gebruikershandleiding) en `uitleg.md` (technische uitleg) in deze module.
