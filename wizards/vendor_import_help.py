from odoo import fields, models


class VendorImportHelp(models.TransientModel):
    _name = "vendor.import.help"
    _description = "Vendor Import Help"

    name = fields.Char(default="Handleiding Vendor Import", readonly=True)
    content = fields.Html(
        readonly=True,
        sanitize=False,
        translate=False,
        default=lambda self: self._default_content(),
    )

    @staticmethod
    def _default_content():
        # Korte uitleg + ChatGPT-prompt uit de handleiding, zodat gebruikers
        # vanuit Odoo zelf de tekst kunnen kopiëren.
        return """
<h2>Handleiding Vendor Import & ChatGPT-prompt</h2>
<p>
Deze pop-up geeft een korte uitleg over de Vendor Import-module en bevat
een kant-en-klare prompt om in ChatGPT te plakken. Daarmee kun je op basis
van een Excelbestand automatisch een voorstel laten doen voor een
<em>importprofiel</em> (kolommapping per leverancier/merk).
</p>

<h3>Stap 1: Kolomkoppen uit Excel verzamelen</h3>
<p>
Open het Excelbestand van de leverancier (bijvoorbeeld Houweling) en kopieer
de kolomkoppen (eerste rij) of een voorbeeld van de eerste rij naar je klembord.
</p>

<h3>Stap 2: Gebruik deze prompt in ChatGPT</h3>
<p>Kopieer onderstaande tekst in ChatGPT en plak daaronder de kolomkoppen.</p>

<pre style="white-space: pre-wrap;">
Je bent een Odoo 18 / data-import specialist. Ik gebruik een maatwerkmodule "Vendor Import" met importprofielen.

Op basis van de kolomkoppen in dit Excelbestand wil ik een voorstel voor een importprofiel krijgen.

Belangrijk:
- Elk importprofiel hoort bij één leverancier/merk.
- Een profiel bestaat uit regels met:
  - rol (role)
  - Excel-kolomtitel of patroon (header_pattern)
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
2) Stel een mapping voor van Excel-kolomtitel → rol.
3) Geef het resultaat terug als een nette tabel met kolommen: role, header_pattern, required, opmerkingen.
4) Markeer alleen echt cruciale kolommen als required (zoals product_name, brand, sku of barcode, purchase_price, image_main als er productfoto's zijn).
5) Voeg onder de tabel een korte toelichting toe (in het Nederlands) waarom je bepaalde keuzes hebt gemaakt en welke kolommen je bewust leeg hebt gelaten.

Gebruik geen code, maar alleen tekst en tabellen in Markdown-vorm.
Als iets onduidelijk is (bijvoorbeeld meerdere mogelijke kolommen voor kleur of maat), stel dan eerst verduidelijkende vragen voordat je de definitieve mapping geeft.
</pre>

<h3>Stap 3: Profiel in Odoo invullen</h3>
<p>
Ga naar <strong>Voorraad → Vendor Import → Importprofielen</strong> en maak een nieuw profiel aan voor de leverancier.
</p>
<p>
<strong>Nieuwe verbeterde methode:</strong> Plak de kolomkoppen direct in het veld "Voorbeeld Kolomkoppen" en klik op "Suggest Mapping" voor automatische voorstellen. Controleer en pas de mapping aan waar nodig.
</p>
<p>
Als je de oude ChatGPT-methode wilt gebruiken, neem dan de voorgestelde tabel uit ChatGPT over in de kolommapping.
</p>
"""
