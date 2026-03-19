import re

from odoo import api, fields, models, _
import logging


_logger = logging.getLogger(__name__)


class VendorCategoryRule(models.Model):
    _name = "vendor.category.rule"
    _description = "Vendor Category Rule"

    # Shared selection for vendor_code and test_vendor_code
    @api.model
    def _selection_vendor_code(self):
        return [
            ("tgh", "TGH"),
            ("houweling", "Houweling"),
            ("any", "Alle leveranciers"),
        ]

    name = fields.Char(string="Naam", required=True)
    active = fields.Boolean(string="Actief", default=True)

    vendor_code = fields.Selection(
        selection=lambda self: self._selection_vendor_code(),
        string="Leverancier",
        default="any",
        required=True,
    )

    match_type = fields.Selection(
        selection=[
            ("contains", "Bevat"),
            ("startswith", "Begint met"),
            ("regex", "Regex"),
        ],
        string="Match type",
        default="contains",
        required=True,
    )

    keyword = fields.Char(string="Zoekwoord / patroon", required=True)

    priority = fields.Integer(
        string="Prioriteit", default=10, help="Hogere waarde wint bij meerdere matches."
    )

    category_id = fields.Many2one(
        comodel_name="product.category",
        string="Categorie",
        required=True,
    )

    audience = fields.Selection(
        selection=[
            ("men", "Heren"),
            ("women", "Dames"),
            ("kids", "Kids"),
            ("unisex", "Unisex"),
            ("any", "Alle doelgroepen"),
        ],
        string="Doelgroep",
        default="any",
    )

    notes = fields.Text(string="Notities")

    # Testomgeving velden (niet-persistent, maar gewone velden is eenvoudiger)
    test_product_name = fields.Char(
        string="Test productnaam",
        help="Voer een voorbeeld productnaam in om de categorie-regel engine te testen.",
    )
    test_vendor_code = fields.Selection(
        selection=lambda self: self._selection_vendor_code(),
        string="Test leverancier",
        default="any",
        help=(
            "Kies welke leverancier-context je wilt simuleren tijdens het testen "
            "van de categorie-regels."
        ),
    )
    test_result = fields.Text(
        string="Testresultaat",
        readonly=True,
        help="Resultaat van de laatste test van de categorie-regel engine.",
    )

    _sql_constraints = [
        (
            "vendor_category_rule_unique",
            "unique(vendor_code, keyword, category_id, audience)",
            "Er bestaat al een categorie-regel met dezelfde leverancier, zoekwoord, categorie en doelgroep.",
        ),
    ]

    # ============================================================
    # Hulpfuncties voor categorie-structuur
    # ============================================================

    @api.model
    def _get_or_create_category_by_path(self, path):
        """Zoek of maak een product.category boom op basis van een pad.

        Voorbeeld: "Bedrijfskleding / T-Shirts" creëert (indien nodig):
        - Bedrijfskleding
        - T-Shirts onder Bedrijfskleding

        Zorgt dat er geen dubbele namen onder dezelfde parent ontstaan.
        """

        if not path:
            return self.env["product.category"]

        Category = self.env["product.category"]
        names = [p.strip() for p in str(path).split("/") if p and str(p).strip()]
        parent = Category.browse(False)

        for name in names:
            domain = [("name", "=", name)]
            if parent:
                domain.append(("parent_id", "=", parent.id))
            else:
                domain.append(("parent_id", "=", False))

            category = Category.search(domain, limit=1)
            if not category:
                vals = {"name": name}
                if parent:
                    vals["parent_id"] = parent.id
                category = Category.create(vals)
                _logger.info(
                    "Created product.category '%s' under parent '%s' for path '%s'",
                    name,
                    parent.display_name if parent else "(root)",
                    path,
                )
            parent = category

        return parent

    # ============================================================
    # Seed default rules
    # ============================================================

    def action_seed_default_rules(self):
        """Maak standaard EMENER categorie-regels aan indien nog niet aanwezig.

        - Geen duplicaten (controle op keyword + category + vendor_code).
        - vendor_code = "any", match_type = "contains", priority = 50.
        """

        self.ensure_one()

        default_definitions = [
            ("t-shirt", "Bedrijfskleding / T-Shirts"),
            ("poloshirt", "Bedrijfskleding / Polo's"),
            ("polo", "Bedrijfskleding / Polo's"),
            ("softshell", "Bedrijfskleding / Jassen / Softshell"),
            ("fleece", "Bedrijfskleding / Jassen / Fleece"),
            ("bodywarmer", "Bedrijfskleding / Bodywarmers"),
            ("jacket", "Bedrijfskleding / Jassen"),
            ("windjacket", "Bedrijfskleding / Jassen"),
            ("3-in-1", "Bedrijfskleding / Jassen"),
            ("hooded", "Bedrijfskleding / Sweaters & Hoodies"),
            ("sweater", "Bedrijfskleding / Sweaters & Hoodies"),
            ("sweatjacket", "Bedrijfskleding / Vesten"),
            ("zipneck", "Bedrijfskleding / Vesten"),
            ("beanie", "Bedrijfskleding / Accessoires"),
            ("apron", "Bedrijfskleding / Accessoires"),
        ]

        created = 0
        for keyword, path in default_definitions:
            category = self._get_or_create_category_by_path(path)
            if not category:
                continue

            existing = self.search(
                [
                    ("vendor_code", "=", "any"),
                    ("keyword", "=", keyword),
                    ("category_id", "=", category.id),
                ],
                limit=1,
            )
            if existing:
                continue

            rule_vals = {
                "name": _("Standaardregel: %s") % keyword,
                "active": True,
                "vendor_code": "any",
                "match_type": "contains",
                "keyword": keyword,
                "priority": 50,
                "category_id": category.id,
            }
            self.create(rule_vals)
            created += 1

        _logger.info("Seeded %s default vendor.category.rule records", created)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Categorie regels"),
                "message": _("Standaardregels aangemaakt: %s") % created,
                "type": "success",
                "sticky": False,
            },
        }

    # ============================================================
    # Test regel engine
    # ============================================================

    def action_test_rule_engine(self):
        """Test de categorie-regel engine met een voorbeeldnaam en leverancier."""
        self.ensure_one()

        product_name = (self.test_product_name or "").strip()
        vendor_code = (self.test_vendor_code or "any").lower()

        if not product_name:
            self.test_result = _("Geen test productnaam ingevuld.")
            return False

        rule = self.env["vendor.category.rule"].match(product_name, vendor_code)

        if not rule:
            self.test_result = _("Geen match gevonden.")
            return False

        category_path_parts = []
        category = rule.category_id
        while category:
            category_path_parts.append(category.name or "")
            category = category.parent_id
        category_path = (
            " / ".join(reversed(category_path_parts)) if category_path_parts else ""
        )

        result_lines = [
            _("Match gevonden"),
            "-------------------",
            _("Regel: %s") % (rule.name or ""),
            _("Zoekwoord: %s") % (rule.keyword or ""),
            _("Categorie: %s") % category_path,
            _("Prioriteit: %s") % (rule.priority or 0),
            _("Doelgroep: %s")
            % (
                dict(self._fields["audience"].selection).get(
                    rule.audience, rule.audience or ""
                )
            ),
        ]

        self.test_result = "\n".join(result_lines)
        return False

    @api.model
    def _detect_audience(self, name):
        """Detecteer doelgroep op basis van tekst in productnaam."""
        if not name:
            return "any"
        text = name.lower()

        men_tokens = ["men's", "mens", "men´s", " men ", " heren ", "heren"]
        women_tokens = ["women's", "womens", "ladies", " women ", " dames ", "dames"]
        kids_tokens = ["kids", " kid ", "children", " kind ", "kinderen"]
        unisex_tokens = ["unisex"]

        for token in men_tokens:
            if token.strip() and token.strip() in text:
                return "men"
        for token in women_tokens:
            if token.strip() and token.strip() in text:
                return "women"
        for token in kids_tokens:
            if token.strip() and token.strip() in text:
                return "kids"
        for token in unisex_tokens:
            if token.strip() and token.strip() in text:
                return "unisex"
        return "any"

    @api.model
    def match(self, product_name, vendor_code):
        """Zoek de beste categorie-regel voor deze productnaam en leverancier.

        - vendor_code: code zoals 'tgh', 'houweling' of 'any'.
        - product_name: de naam die voor de template gebruikt wordt.
        """
        if not product_name:
            return self.browse()

        vendor_code = (vendor_code or "any").lower()
        name_l = product_name.lower()

        domain = [
            ("active", "=", True),
            ("vendor_code", "in", [vendor_code, "any"]),
        ]
        rules = self.search(domain)
        if not rules:
            return self.browse()

        detected_audience = self._detect_audience(product_name)

        best_rule = None
        best_priority = None
        best_keyword_len = None

        for rule in rules:
            # Audience filter
            if (
                rule.audience
                and rule.audience != "any"
                and detected_audience != rule.audience
            ):
                continue

            keyword = (rule.keyword or "").lower().strip()
            if not keyword:
                continue

            matched = False
            if rule.match_type == "contains":
                matched = keyword in name_l
            elif rule.match_type == "startswith":
                matched = name_l.startswith(keyword)
            elif rule.match_type == "regex":
                try:
                    if re.search(rule.keyword, product_name, flags=re.IGNORECASE):
                        matched = True
                except re.error:
                    # Ongeldige regex: sla regel over
                    matched = False

            if not matched:
                continue

            # Bepaal score: hoogste priority, dan langste keyword
            kw_len = len(keyword)
            prio = rule.priority or 0

            if best_rule is None:
                best_rule = rule
                best_priority = prio
                best_keyword_len = kw_len
                continue

            if prio > best_priority:
                best_rule = rule
                best_priority = prio
                best_keyword_len = kw_len
            elif prio == best_priority and kw_len > (best_keyword_len or 0):
                best_rule = rule
                best_keyword_len = kw_len

        return best_rule or self.browse()
