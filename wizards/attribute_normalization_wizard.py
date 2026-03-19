from odoo import models, fields, api


class AttributeNormalizationWizard(models.TransientModel):
    _name = "attribute.normalization.wizard"
    _description = "Attribute Normalization Wizard"

    name = fields.Char(string="Name", required=True)

    def action_confirm(self):
        # Placeholder for future logic
        return True
