from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    vendor_import_excel_manual_html = fields.Html(
        string="Vendor Import Manual",
        help="Instructions for how the vendor's Excel file columns should be named for imports.",
    )
