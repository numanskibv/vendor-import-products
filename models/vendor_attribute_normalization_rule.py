from odoo import fields, models, api


class VendorAttributeNormalizationRule(models.Model):
    _name = "vendor.attribute.normalization.rule"
    _description = "Vendor Attribute Normalization Rule"
    _order = "vendor_id, attribute_type, raw_value"

    vendor_id = fields.Many2one(
        comodel_name="res.partner",
        string="Leverancier",
        domain=[("supplier_rank", ">", 0)],
        help="Regel is van toepassing op deze leverancier. Laat leeg voor een algemene regel.",
    )
    attribute_type = fields.Selection(
        [("color", "Kleur"), ("size", "Maat")],
        string="Attribuut Type",
        required=True,
    )
    raw_value = fields.Char(string="Ruwe Waarde", required=True, index=True)
    normalized_value = fields.Char(
        string="Genormaliseerde Waarde", required=True, index=True
    )

    _sql_constraints = [
        (
            "unique_rule",
            "UNIQUE(vendor_id, attribute_type, raw_value)",
            "Een normalisatieregel voor deze leverancier, attribuut en ruwe waarde bestaat al.",
        )
    ]
