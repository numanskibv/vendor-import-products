from odoo import api, fields, models, _


class ProductBrand(models.Model):
    _name = "product.brand"
    _description = "Product Brand"

    name = fields.Char(string="Naam", required=True, index=True)
    vendor_id = fields.Many2one(
        comodel_name="res.partner",
        string="Leverancier",
        help="Optioneel: koppel dit merk aan een specifieke leverancier.",
    )
    active = fields.Boolean(string="Actief", default=True)

    _sql_constraints = [
        (
            "product_brand_name_unique",
            "unique(name)",
            "Er bestaat al een merk met deze naam.",
        ),
    ]
