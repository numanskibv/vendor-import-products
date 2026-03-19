from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    brand_id = fields.Many2one(
        comodel_name="product.brand",
        string="Merk",
        help="Merk van het product, gebruikt bij vendor imports.",
    )
