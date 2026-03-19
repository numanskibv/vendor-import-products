from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    vendor_import_default_margin = fields.Float(
        string="Default vendor import margin (%)",
        config_parameter="vendor_import_module.default_margin_percentage",
        default=30.0,
        help=(
            "Default margin percentage used by the vendor import wizard when "
            "creating new imports. Users can still override it per import."
        ),
    )

    vendor_import_template_image_only = fields.Boolean(
        string="Alleen hoofdafbeelding per product (geen variantfoto's)",
        config_parameter="vendor_import_module.template_image_only",
        help=(
            "Als dit aan staat, slaat de import alleen een hoofdafbeelding per "
            "producttemplate op. Variant-specifieke afbeeldingen per maat/kleur "
            "worden overgeslagen om schijfruimte te besparen."
        ),
    )
