from odoo import api, fields, models, _


class VendorImportProfile(models.Model):
    _name = "vendor.import.profile"
    _description = "Vendor Import Profile"

    name = fields.Char(string="Naam", required=True)
    active = fields.Boolean(default=True)

    vendor_id = fields.Many2one(
        comodel_name="res.partner",
        string="Leverancier",
        help=(
            "Optioneel: beperk dit profiel tot een specifieke leverancier. "
            "Laat leeg om het profiel voor meerdere leveranciers te kunnen gebruiken."
        ),
    )
    code = fields.Char(
        string="Profielcode",
        help=(
            "Interne code om dit profiel te herkennen vanuit de importwizard, bijv. 'tgh', 'xyz_brand'."
        ),
    )
    file_prefix = fields.Char(
        string="Bestandsnaamprefix",
        help=(
            "Optioneel: als ingevuld wordt het profiel alleen gesuggereerd als de bestandsnaam hiermee begint."
        ),
    )

    line_ids = fields.One2many(
        comodel_name="vendor.import.profile.line",
        inverse_name="profile_id",
        string="Kolommapping",
    )

    example_headers = fields.Text(
        string="Voorbeeld Kolomkoppen",
        help=(
            "Plak hier de eerste rij (kolomkoppen) uit het Excel-bestand van de leverancier. "
            "Gebruik daarna de 'Suggest Mapping' button om automatisch een voorstel te krijgen voor de kolommapping."
        ),
    )

    @api.model
    def match_profile(self, *, vendor, filename, headers_raw, norm_func):
        """Vind een importprofiel en kolommapping voor de gegeven headers.

        Geeft een tuple (profile, role_to_index, image_indices) terug of
        (False, {}, []) als er geen passend profiel is.

        - vendor: res.partner record (of False)
        - filename: bestandsnaam (str)
        - headers_raw: lijst van originele kolomkoppen
        - norm_func: functie die een kop normaliseert (zoals _norm_header)
        """
        Profile = self.env["vendor.import.profile"].sudo()
        profiles = Profile.search([("active", "=", True)])

        # Filter op vendor
        if vendor:
            vendor_profiles = profiles.filtered(lambda p: p.vendor_id == vendor)
            if vendor_profiles:
                profiles = vendor_profiles

        # Filter op filename prefix
        if filename and any(p.file_prefix for p in profiles):

            def _match_prefix(profile):
                if not profile.file_prefix:
                    return False
                return filename.startswith(profile.file_prefix)

            profiles = profiles.filtered(_match_prefix)

        if not profiles:
            return False, {}, []

        # Try every profile and pick the best match.
        # Rationale: multiple profiles may match the same vendor/prefix.
        # We prefer the profile that matches the most roles and has the most
        # specific filename prefix.
        best = None
        best_role_to_index = {}
        best_image_indices = []

        headers_norm = [norm_func(h) for h in (headers_raw or [])]

        for profile in profiles:
            role_to_index = {}
            image_indices = []
            missing_required = []

            for line in profile.line_ids:
                pattern_norm = norm_func(line.header_pattern or "")
                if not pattern_norm:
                    # Avoid accidental matches like an empty pattern matching everything.
                    continue

                found_idx = None
                for idx, h_norm in enumerate(headers_norm):
                    if h_norm.startswith(pattern_norm) or pattern_norm in h_norm:
                        found_idx = idx
                        break

                if found_idx is not None:
                    role_to_index[line.role] = found_idx
                    if (line.role or "").startswith("image_"):
                        if found_idx not in image_indices:
                            image_indices.append(found_idx)
                elif line.required:
                    missing_required.append(line.role)

            # Profiles that miss required mappings are not eligible.
            if missing_required:
                continue

            # Score: prefer many role matches; tie-breaker: more specific prefix.
            # We include image_indices in score because it matters for image imports.
            role_score = len(role_to_index)
            image_score = len(image_indices)
            prefix_len = len((profile.file_prefix or "").strip())
            score = (role_score, image_score, prefix_len)

            if best is None or score > best:
                best = score
                best_role_to_index = role_to_index
                best_image_indices = image_indices
                best_profile = profile

        if best is None:
            return False, {}, []

        return best_profile, best_role_to_index, best_image_indices

    def action_suggest_mapping(self):
        """Genereer automatische suggesties voor kolommapping op basis van voorbeeld headers."""
        self.ensure_one()
        if not self.example_headers:
            raise UserError(_("Vul eerst de voorbeeld kolomkoppen in."))

        headers = [h.strip() for h in self.example_headers.split("\t") if h.strip()]
        if not headers:
            headers = [h.strip() for h in self.example_headers.split(",") if h.strip()]
        if not headers:
            headers = self.example_headers.splitlines()[0].split()  # fallback

        # Normaliseer headers (zelfde als in wizard)
        def _norm_header(header):
            return re.sub(r"[^\w]", "", header.lower())

        norm_headers = [_norm_header(h) for h in headers]

        # Suggesties gebaseerd op veelvoorkomende patronen
        suggestions = []
        role_patterns = {
            "product_name": [
                "productname",
                "artikelnaam",
                "produktname",
                "name",
                "titel",
            ],
            "sku": [
                "sku",
                "artikelnummer",
                "artikelcode",
                "productcode",
                "defaultcode",
            ],
            "brand": ["merk", "brand", "manufacturer"],
            "barcode": ["barcode", "ean", "gtin", "streepjescode"],
            "color": ["kleur", "color", "farbe"],
            "size": ["maat", "size", "groesse", "grootte"],
            "category_name": ["categorie", "category", "kategorie"],
            "purchase_price": [
                "inkoopprijs",
                "purchaseprice",
                "prijsactueel",
                "prijs",
                "price",
                "kosten",
            ],
            "currency": ["valuta", "currency", "munt"],
            "image_main": ["afbeelding", "image", "foto", "picture", "hoofdafbeelding"],
            "image_extra": ["extraafbeelding", "extraimage", "meerfoto"],
            "short_desc_nl": [
                "korteomschrijving",
                "shortdescription",
                "beschrijvingkort",
            ],
            "long_desc_nl": ["langeomschrijving", "longdescription", "beschrijving"],
        }

        for role, patterns in role_patterns.items():
            for idx, norm_h in enumerate(norm_headers):
                if any(p in norm_h for p in patterns):
                    suggestions.append(
                        {
                            "role": role,
                            "header_pattern": headers[idx],
                            "required": role
                            in [
                                "product_name",
                                "purchase_price",
                            ],  # maak sommige verplicht
                        }
                    )
                    break  # neem de eerste match

        # Maak line_ids aan
        self.line_ids = [(5, 0, 0)]  # clear existing
        for sugg in suggestions:
            self.line_ids = [(0, 0, sugg)]

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Suggesties toegevoegd"),
                "message": _(
                    "Automatische mapping-suggesties zijn toegevoegd. Controleer en pas aan indien nodig."
                ),
                "type": "success",
            },
        }
        """Vind een importprofiel en kolommapping voor de gegeven headers.

        Geeft een tuple (profile, role_to_index, image_indices) terug of
        (False, {}, []) als er geen passend profiel is.

        - vendor: res.partner record (of False)
        - filename: bestandsnaam (str)
        - headers_raw: lijst van originele kolomkoppen
        - norm_func: functie die een kop normaliseert (zoals _norm_header)
        """

        Profile = self.env["vendor.import.profile"].sudo()
        profiles = Profile.search([("active", "=", True)])

        if vendor:
            vendor_profiles = profiles.filtered(lambda p: p.vendor_id == vendor)
            if vendor_profiles:
                profiles = vendor_profiles

        filename = (filename or "").strip()
        if filename and any(p.file_prefix for p in profiles):

            def _match_prefix(p):
                if not p.file_prefix:
                    return True
                return filename.startswith(p.file_prefix)

            profiles = profiles.filtered(_match_prefix)

        if not profiles:
            return False, {}, []

        headers_norm = [norm_func(h) for h in headers_raw]

        for profile in profiles:
            role_to_index = {}
            image_indices = []
            ok = True
            for line in profile.line_ids:
                pattern_norm = norm_func(line.header_pattern or "")
                try:
                    idx = headers_norm.index(pattern_norm)
                except ValueError:
                    idx = None

                if idx is None:
                    if line.required:
                        ok = False
                        break
                    continue

                # Bewaar mapping voor deze rol
                role_to_index[line.role] = idx
                if line.role in {"image_main", "image_extra"}:
                    if idx not in image_indices:
                        image_indices.append(idx)

            if ok and role_to_index:
                return profile, role_to_index, image_indices

        return False, {}, []


class VendorImportProfileLine(models.Model):
    _name = "vendor.import.profile.line"
    _description = "Vendor Import Profile Column Mapping"
    _order = "sequence, id"

    profile_id = fields.Many2one(
        comodel_name="vendor.import.profile",
        string="Profiel",
        required=True,
        ondelete="cascade",
    )

    sequence = fields.Integer(default=10)

    role = fields.Selection(
        selection=[
            ("product_name", "Productnaam"),
            ("sku", "SKU / Artikelnummer"),
            ("brand", "Merk"),
            ("barcode", "Barcode / GTIN"),
            ("color", "Kleur"),
            ("size", "Maat"),
            ("category_name", "Categorie"),
            ("purchase_price", "Inkoopprijs"),
            ("currency", "Valuta"),
            ("image_main", "Hoofdafbeelding URL"),
            ("image_extra", "Extra afbeelding URL"),
            ("short_desc_nl", "Korte omschrijving (NL)"),
            ("long_desc_nl", "Lange omschrijving (NL)"),
        ],
        string="Rol",
        required=True,
        help=(
            "Kies de rol die deze Excel-kolom vertegenwoordigt in Odoo:\n"
            "- Productnaam: De naam van het product (verplicht voor nieuwe producten)\n"
            "- SKU / Artikelnummer: Unieke code voor het product\n"
            "- Merk: Merknaam van het product\n"
            "- Barcode / GTIN: Streepjescode voor identificatie\n"
            "- Kleur: Kleurvariant van het product\n"
            "- Maat: Maatvariant van het product\n"
            "- Categorie: Productcategorie\n"
            "- Inkoopprijs: Prijs waarvoor het product wordt ingekocht\n"
            "- Valuta: Valuta van de prijzen (bijv. EUR)\n"
            "- Hoofdafbeelding URL: Link naar de hoofdfoto\n"
            "- Extra afbeelding URL: Link naar extra foto's\n"
            "- Korte omschrijving (NL): Beknopte beschrijving in het Nederlands\n"
            "- Lange omschrijving (NL): Uitgebreide beschrijving in het Nederlands"
        ),
    )

    header_pattern = fields.Char(
        string="Kolomkop (patroon)",
        required=True,
        help=(
            "Tekst of patroon waarmee de genormaliseerde kolomkop wordt vergeleken. "
            "Bijvoorbeeld 'produktname', 'productnaam', 'artikelnaam'."
        ),
    )

    required = fields.Boolean(
        string="Verplicht",
        default=False,
        help="Als aangevinkt, moet deze rol een kolom in het Excelbestand vinden.",
    )

    def describe_mapping(self):
        self.ensure_one()
        return _("Rol '%(role)s' -> patroon '%(pattern)s'") % {
            "role": self.role,
            "pattern": self.header_pattern,
        }
