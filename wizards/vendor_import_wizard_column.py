from odoo import fields, models


class VendorImportWizardColumn(models.TransientModel):
    _name = "vendor.import.wizard.column"
    _description = "Vendor Import Wizard Excel Column"
    _order = "index, id"

    wizard_id = fields.Many2one(
        comodel_name="vendor.import.wizard",
        string="Wizard",
        required=True,
        ondelete="cascade",
        index=True,
    )

    header = fields.Char(string="Header", required=True)
    index = fields.Integer(string="Index", required=True)

    def name_get(self):
        res = []

        wizard_ids = list({r.wizard_id.id for r in self if r.wizard_id})
        all_cols = self.env["vendor.import.wizard.column"].browse()
        if wizard_ids:
            all_cols = self.env["vendor.import.wizard.column"].search(
                [("wizard_id", "in", wizard_ids)], order="index, id"
            )

        # Build occurrence lists per (wizard, header)
        occ = {}
        for col in all_cols:
            key = ((col.wizard_id.id or 0), (col.header or "").strip())
            occ.setdefault(key, []).append(col.id)

        for rec in self:
            header = (rec.header or "").strip() or "(leeg)"
            key = ((rec.wizard_id.id or 0), (rec.header or "").strip())
            ids = occ.get(key) or [rec.id]
            if len(ids) > 1:
                try:
                    pos = ids.index(rec.id) + 1
                except ValueError:
                    pos = 1
                header = f"{header} ({pos})"
            res.append((rec.id, header))
        return res
