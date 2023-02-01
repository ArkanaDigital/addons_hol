from odoo import fields, models, api, SUPERUSER_ID
from odoo.exceptions import ValidationError
from logging import getLogger

_logger = getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    _order = "last_update_openchatter desc,priority desc,activity_date_deadline,id desc"

    @api.constrains('tag_ids')
    def constrains_tag_ids(self):
        for rec in self:
            if len(rec.tag_ids) < 2:
                raise ValidationError('Tags need to be filled with at least 2 values')

    @api.depends("message_ids")
    @api.multi
    def _compute_last_update_openchatter(self):
        for document in self:
            last_update_openchatter = document.create_date
            if (
                len(
                    document.message_ids.filtered(
                        lambda r: r.create_uid.id != SUPERUSER_ID
                    )
                )
                > 0
            ):
                last_update_openchatter = document.message_ids.filtered(
                    lambda r: r.create_uid.id != SUPERUSER_ID
                )[0].create_date
            
            document.last_update_openchatter = last_update_openchatter
            # _logger.info(f'Update last_update_openchatter {document.id}')
