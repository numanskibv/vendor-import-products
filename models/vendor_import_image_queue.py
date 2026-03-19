import base64
import logging
import urllib.request

from odoo import api, fields, models, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class VendorImportImageQueue(models.Model):
    _name = "vendor.import.image.queue"
    _description = "Vendor Import Image Queue"
    _order = "create_date asc, id asc"

    vendor_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier",
        required=True,
        index=True,
        ondelete="cascade",
    )
    url = fields.Char(string="URL", required=True, index=True)
    product_tmpl_id = fields.Many2one(
        comodel_name="product.template",
        string="Product Template",
        required=True,
        index=True,
        ondelete="cascade",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product Variant",
        index=True,
        ondelete="cascade",
    )

    state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("done", "Done"),
            ("error", "Error"),
        ],
        default="pending",
        required=True,
        index=True,
    )
    attempts = fields.Integer(default=0)
    last_error = fields.Text()
    last_try_date = fields.Datetime()
    done_date = fields.Datetime()

    def init(self):
        super().init()
        # Deduplicate jobs even when product_id is NULL (template-level images)
        # by indexing on COALESCE(product_id, 0).
        # Note: Odoo helper create_unique_index doesn't reliably support expression
        # indexes across versions, so we create the index explicitly.
        self._cr.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS vendor_import_image_queue_uniq_job
            ON vendor_import_image_queue (vendor_id, product_tmpl_id, (COALESCE(product_id, 0)), url)
            """
        )

    def _download_image_b64(
        self, url, *, timeout=15, max_bytes=10 * 1024 * 1024, cache=None
    ):
        if not url:
            return None
        cache = cache if cache is not None else {}
        if url in cache:
            return cache[url]

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Odoo Vendor Import (openpyxl)",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content_type = (response.headers.get("Content-Type") or "").lower()
            data = response.read(max_bytes + 1)

        if len(data) > max_bytes:
            cache[url] = None
            raise ValueError("Image too large")

        if content_type and not content_type.startswith("image/"):
            cache[url] = None
            raise ValueError(f"Not an image (content-type={content_type})")

        result = base64.b64encode(data)
        cache[url] = result
        return result

    def _apply_image(self, *, url, image_b64, ProductImage):
        self.ensure_one()

        template = self.product_tmpl_id
        variant = self.product_id

        # Template main image
        if not variant and "image_1920" in template._fields and not template.image_1920:
            template.write({"image_1920": image_b64})

        # Variant main image
        if variant and "image_1920" in variant._fields and not variant.image_1920:
            variant.write({"image_1920": image_b64})

        # Extra images model (product.image), if available
        if ProductImage is None:
            return

        if "product_tmpl_id" not in ProductImage._fields:
            return

        if variant and "product_variant_id" in ProductImage._fields:
            domain = [
                ("product_tmpl_id", "=", template.id),
                ("product_variant_id", "=", variant.id),
                ("name", "=", url),
            ]
            if not ProductImage.search(domain, limit=1):
                vals = {
                    "name": url,
                    "product_tmpl_id": template.id,
                    "product_variant_id": variant.id,
                    "image_1920": image_b64,
                }
                ProductImage.create(vals)
            return

        # Template-level extra image
        domain = [("product_tmpl_id", "=", template.id), ("name", "=", url)]
        if not ProductImage.search(domain, limit=1):
            vals = {
                "name": url,
                "product_tmpl_id": template.id,
                "image_1920": image_b64,
            }
            ProductImage.create(vals)

    @api.model
    def _process_pending_jobs(self, *, domain=None, limit=None):
        icp = self.env["ir.config_parameter"].sudo()
        batch_size = int(
            icp.get_param("vendor_import_module.image_batch_size", "20") or 20
        )
        max_attempts = int(
            icp.get_param("vendor_import_module.image_max_attempts", "3") or 3
        )

        limit = int(limit or batch_size)
        domain = list(domain or [])
        domain += [("state", "=", "pending"), ("attempts", "<", max_attempts)]

        queue = self.env["vendor.import.image.queue"].sudo()
        jobs = queue.search(domain, limit=limit)
        if not jobs:
            return {"done": 0, "failed": 0, "total": 0}

        try:
            ProductImage = self.env["product.image"].sudo()
        except KeyError:
            ProductImage = None

        cache = {}
        done = 0
        failed = 0

        for job in jobs:
            try:
                image_b64 = job._download_image_b64(job.url, cache=cache)
                if not image_b64:
                    raise ValueError("Empty image")
                job._apply_image(
                    url=job.url, image_b64=image_b64, ProductImage=ProductImage
                )
                job.write(
                    {
                        "state": "done",
                        "done_date": fields.Datetime.now(),
                        "last_error": False,
                    }
                )
                done += 1
            except Exception as exc:
                attempts = (job.attempts or 0) + 1
                values = {
                    "attempts": attempts,
                    "last_try_date": fields.Datetime.now(),
                    "last_error": str(exc),
                }
                # Permanent errors (not an image / too large) -> mark error immediately.
                msg = str(exc).lower()
                if "not an image" in msg or "image too large" in msg:
                    values["state"] = "error"
                elif attempts >= max_attempts:
                    values["state"] = "error"
                job.write(values)
                failed += 1

        _logger.info(
            "Vendor image cron processed queue: done=%s failed=%s (batch=%s)",
            done,
            failed,
            limit,
        )

        return {"done": done, "failed": failed, "total": len(jobs)}

    @api.model
    def _cron_process_queue(self):
        return self._process_pending_jobs()

    def action_reset_vendor_queue(self):
        """Verwijder alle image-queue taken voor de leverancier van dit record."""
        self.ensure_one()
        if not self.vendor_id:
            raise UserError(_("Selecteer eerst een leverancier."))

        queue = self.env["vendor.import.image.queue"].sudo()
        domain = [("vendor_id", "=", self.vendor_id.id)]
        jobs = queue.search(domain)
        count = len(jobs)
        if count:
            jobs.unlink()

        message = _(
            "Afbeeldingenwachtrij leeggemaakt voor %(vendor)s. Verwijderde taken: %(count)s"
        ) % {
            "vendor": self.vendor_id.display_name,
            "count": count,
        }

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Afbeeldingenwachtrij"),
                "message": message,
                "type": "info",
                "sticky": False,
            },
        }
