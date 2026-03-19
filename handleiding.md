# Handleiding Vendor Import

Deze handleiding beschrijft hoe je de Vendor Import‑wizard gebruikt om leveranciers‑Excelbestanden te importeren. TGH is daarbij een belangrijk voorbeeld, maar via **Importprofielen** kun je ook andere leveranciers/merken met een eigen Excel‑indeling ondersteunen.

## 1. Voorbereiding

1. Zorg dat de module **Vendor Import Module** is geïnstalleerd.
2. Maak (indien nodig) een **Importprofiel** aan voor de leverancier/merk:
   - Ga naar **Voorraad → Vendor Import → Importprofielen**.
   - Maak een nieuw profiel voor de gewenste leverancier en stel eventueel een bestandsnaamprefix in.
   - Voeg regels toe in het tabblad voor kolommapping (welke Excel‑kolom hoort bij welke rol, zoals productnaam, merk, kleur, maat, barcode, inkoopprijs, hoofdafbeelding, extra afbeelding, enz.).
3. Open de betreffende leverancier (bijv. TGH) bij **Contacten** en vul de **Vendor Import handleiding** in (tekst/HTML met uitleg over kolomnamen).
4. Controleer dat het Excelbestand de vereiste kolommen bevat (zoals beschreven in de handleiding op de leverancier en in het importprofiel).

> Tip: onder **Voorraad → Vendor Import → Instellingen** kun je behalve de standaardmarge ook instellen of er alleen een hoofdafbeelding per producttemplate gebruikt moet worden (geen aparte variantfoto's per maat/kleur).

> Extra hulp: onder **Voorraad → Vendor Import → Handleiding &amp; prompt** vind je dezelfde uitleg en een kant-en-klare ChatGPT-prompt in een popup binnen Odoo zelf.

## 2. Wizard openen

1. Ga naar **Voorraad → Vendor Import → Import leveranciers‑Excel**.
2. De wizard opent in een popup met twee tabbladen: **Importeer** en **Analyse**.

## 3. Tab "Importeer"

Velden:

- **Supplier** – kies de leverancier (bijv. TGH). Verplicht.
- **File** – upload het TGH‑Excelbestand.
- **Margin (%)** – marge waarmee verkoopprijzen berekend worden.
- **Overwrite Prices** – overschrijf bestaande prijzen in Odoo, ook als ze al gevuld zijn.
- **Archive Missing Variants** – archiveer varianten die niet meer in het Excelbestand voorkomen.
- **Publish Products on Website** – publiceer producten op de website als het Excel dit aangeeft.
- **Apply Category Rules** – pas categorie‑regels toe op nieuwe templates of templates zonder categorie.
- **Create New Categories** – maak nieuwe productcategorieën aan op basis van een categoriekolom in Excel.
- **Category scan column name** – plak hier de Excel‑kolomnaam (header) die gebruikt moet worden om categorieën te bepalen (bijv. `Categorie`).

Onder in de wizard:

- **TGH import – kolomnamen** – tekst uit de handleiding op de leverancier.
- **IMAGE QUEUE** – tellers van openstaande, verwerkte en foutieve image‑jobs.

## 4. Testen vóór import

1. Upload het Excelbestand en controleer de opties.
2. Klik op **Test**.
3. De wizard:
   - Leest het Excelbestand in.
   - Controleert bestandsnaam versus leveranciersreferentie.
   - Controleert verplichte kolommen en data.
   - Simuleert de import zonder data in Odoo te wijzigen.
4. Bekijk het **Test report** onder in de wizard.

Ga pas verder als het test‑rapport geen blokkerende fouten meer toont.

> Opmerking: als er een passend importprofiel bestaat voor de gekozen leverancier en het bestand (op basis van bestandsnaamprefix en kolomtitels), wordt dat profiel automatisch gebruikt om de juiste kolommen te vinden. Alleen als er geen geschikt profiel is, valt de wizard terug op de standaard TGH‑indeling.

## 5. Analyse‑tab voor categorie‑regels

1. Ga naar het tabblad **Analyse**.
2. Vul indien nodig:
   - **Allow creating draft rules** – aanvinken als je conceptregels wilt laten aanmaken.
   - **Draft vendor code** – leveranciercode voor nieuwe regels (bv. `tgh`).
   - **Base priority for drafts** – basisprioriteit (hoger = belangrijker).
   - **Draft rules active** – alleen aanvinken als conceptregels direct actief mogen zijn.
3. Klik op **Analyse**.
4. De wizard toont in **Analysis report** o.a.:
   - Aantal productnamen met match op categorie‑regel.
   - Aantal namen zonder match.
   - Voorbeelden van namen zonder match.
5. Klik op **Create draft rules** (indien aangevinkt) om conceptregels aan te maken.
6. Ga naar **Voorraad → Vendor Import → Categorie regels** om de `AUTO:`‑regels te bekijken, categorie aan te passen en regels te activeren.

## 6. Producten importeren

1. Zorg dat **Test** succesvol is uitgevoerd met hetzelfde bestand.
2. Klik op **Importeer** in de wizard.
3. De wizard zal:
   - Nieuwe producttemplates en varianten aanmaken.
   - Bestaande varianten bijwerken (prijzen, barcode, SKU, etc.).
   - Varianten archiveren als ze niet meer in het Excelbestand staan (als aangevinkt).
   - Categorie‑regels toepassen op nieuwe templates of templates zonder categorie.
   - Categorieën aanmaken op basis van Excel (optioneel).
   - Merken (`product.brand`) koppelen.
   - Leveranciersinfo (`product.supplierinfo`) bijwerken.
   - Afbeeldingen inplannen in de image queue.

De wizard toont na afloop een samenvattende melding met aantallen aangemaakte/bijgewerkte/geverifieerde records.

## 7. Afbeeldingen verwerken

### 7.1 Image queue begrijpen

- Elke unieke afbeelding‑URL in het Excelbestand wordt als job in de **image queue** gezet.
- Gedeelde foto’s per producttemplate worden één keer ingepland op template‑niveau.
- Variant‑specifieke foto’s (andere URL dan de template) krijgen eigen jobs.
- De blok **IMAGE QUEUE** in de wizard toont:
  - **Images pending** – nog te verwerken jobs.
  - **Images done** – succesvol verwerkte jobs.
  - **Images error** – jobs die definitief zijn mislukt.
  - **Images total** – totaal aantal jobs.

### 7.2 Direct verwerken

- Klik op **Process images now** om direct een batch images te laten downloaden en toepassen.
- De module gebruikt een batchgrootte en maximum retries die via systeemparameters aangepast kunnen worden.

### 7.3 Queue resetten

- Met **Reset image queue** verwijder je alle image‑jobs voor de geselecteerde leverancier.
- Gebruik dit alleen als je echt opnieuw wilt beginnen (bijvoorbeeld na een grote Excel‑wijziging).
- Na reset springen de tellers in **IMAGE QUEUE** meteen naar de actuele waarde (meestal 0).

> Let op: als in de instellingen **Alleen hoofdafbeelding per product (geen variantfoto's)** is aangevinkt, wordt per producttemplate slechts één afbeelding‑URL ingepland en worden variantfoto's overgeslagen. Dit vermindert het aantal jobs en de benodigde opslag aanzienlijk.

### 7.4 Afbeeldingenwachtrij scherm

- Ga naar **Voorraad → Vendor Import → Afbeeldingenwachtrij**.
- In dit scherm kun je:
   - filteren op leverancier, product en status (In wachtrij / Gereed / Fout),
   - groeperen per leverancier of per status,
   - een individuele taak openen om details en foutmeldingen te bekijken.
- In het formulier van een taak staat een knop **Reset queue voor leverancier**:
   - deze wist alle image‑jobs voor die leverancier (net als de reset‑knop in de wizard),
   - handig als je vanuit het overzicht merkt dat de queue “vast” zit of je volledig opnieuw wilt beginnen voor een leverancier.

## 8. Veelvoorkomende foutmeldingen (vertalingen)

Enkele voorbeelden van foutmeldingen en hun betekenis:

- **"Upload een bestand om te importeren."** – er is geen Excelbestand geselecteerd.
- **"Selecteer een leverancier."** – het veld Supplier is leeg.
- **"Verkeerd bestand voor de geselecteerde leverancier"** – de bestandsnaam begint niet met de leveranciersreferentie (bijv. `TGH`).
- **"Kolom X ontbreekt in het Excelbestand"** – een verplichte kolom is niet gevonden.
   - Controleer of je importprofiel en het Excelbestand dezelfde kolomtitels gebruiken.
- **"Python‑package openpyxl is vereist"** – de systeembeheerder moet `openpyxl` installeren in de Odoo‑omgeving.

Zie ook `uitleg.md` voor technische details over hoe deze controles zijn geïmplementeerd.

## 9. Hulpmiddel: prompt om een importprofiel te laten voorstellen (ChatGPT)

Voor leveranciers als Houweling, waar de Excel‑indeling per merk kan verschillen, kun je een AI‑tool (zoals ChatGPT) gebruiken om snel een voorstel voor een importprofiel te laten maken. Onderstaande prompt kun je kopiëren en gebruiken als uitgangspunt.

Plak in ChatGPT eerst de kolomkoppen (of een voorbeeld van de eerste rij) uit het Excelbestand en gebruik dan bijvoorbeeld deze prompt:

```text
Je bent een Odoo 18 / data‑import specialist. Ik gebruik een maatwerkmodule "Vendor Import" met importprofielen.

Op basis van de kolomkoppen in dit Excelbestand wil ik een voorstel voor een importprofiel krijgen.

Belangrijk:
- Elk importprofiel hoort bij één leverancier/merk.
- Een profiel bestaat uit regels met:
   - rol (role)
   - Excel‑kolomtitel of patroon (header_pattern)
   - verplicht of optioneel (required: yes/no)
- Rollen die de module o.a. kent (je mag er meerdere gebruiken als ze logisch zijn):
   - product_name
   - brand
   - sku
   - barcode
   - color
   - size
   - purchase_price
   - currency
   - category_name
   - image_main
   - image_extra
   - description_short_nl
   - description_long_nl

Opdracht:
1) Bekijk de kolomkoppen die ik heb aangeleverd (let op: taal kan Nederlands, Duits of Engels zijn).
2) Stel een mapping voor van Excel‑kolomtitel → rol.
3) Geef het resultaat terug als een nette tabel met kolommen: role, header_pattern, required, opmerkingen.
4) Markeer alleen echt cruciale kolommen als required (zoals product_name, brand, sku of barcode, purchase_price, image_main als er productfoto's zijn).
5) Voeg onder de tabel een korte toelichting toe (in het Nederlands) waarom je bepaalde keuzes hebt gemaakt en welke kolommen je bewust leeg hebt gelaten.

Gebruik geen code, maar alleen tekst en tabellen in Markdown‑vorm.
Als iets onduidelijk is (bijvoorbeeld meerdere mogelijke kolommen voor kleur of maat), stel dan eerst verduidelijkende vragen voordat je de definitieve mapping geeft.
```

Je kunt het resultaat van ChatGPT vervolgens overnemen in het Odoo‑scherm **Voorraad → Vendor Import → Importprofielen** door per regel de juiste rol en kolomtitel in te vullen.

## 10. Importprofielen en kolommappings via Excel importeren

Als je veel regels hebt (bijvoorbeeld meerdere profielen voor TGH en Houweling), is het sneller om de kolommapping in Excel te beheren en via de standaard Odoo‑import te laden.

Globale stappen:

1. Maak eerst de profielen aan in Odoo
   - Ga naar **Voorraad → Vendor Import → Importprofielen**.
   - Maak per profiel een record met een duidelijke naam (bijv. `tgh_standard`, `houweling_image`, enz.).
   - Koppel de juiste leverancier en eventueel een bestandsnaamprefix.

2. Bouw in Excel een tabel met kolommen (PROFILE_LINES)
   - `profile_id`      – de exacte profielnaam zoals in Odoo (Profiel), bijvoorbeeld `tgh_standard`.
   - `sequence`        – volgorde (10, 20, 30, …).
   - `role`            – één van de rollen: `product_name`, `brand`, `sku`, `barcode`, `color`, `size`, `purchase_price`, `currency`, `category_name`, `image_main`, `image_extra`, `short_desc_nl`, `long_desc_nl`.
   - `header_pattern`  – de Excel‑kolomtitel die bij deze rol hoort.
   - `required`        – 1 of 0 (verplicht ja/nee).
   - `remark`          – optionele toelichting (wordt niet geïmporteerd).

3. Importeer de kolommappings in Odoo
   - Ga naar **Instellingen → Technisch → Modellen → vendor.import.profile.line**.
   - Klik op **Importeren** en kies je Excelbestand.
   - Koppel de kolommen als volgt:
     - `profile_id`     → veld **Profiel** (Many2one, zoeken op naam).
     - `sequence`       → veld **Volgorde**.
     - `role`           → veld **Rol**.
     - `header_pattern` → veld **Kolomkop (patroon)**.
     - `required`       → veld **Verplicht**.
     - `remark`         → niet mappen.

Na het importeren kun je in **Importprofielen** de regels nog per profiel bekijken en eventueel handmatig bijwerken.
