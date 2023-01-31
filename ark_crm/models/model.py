from odoo import fields, models, api
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.constrains('tag_ids')
    def constrains_tag_ids(self):
        for rec in self:
            if len(rec.tag_ids) < 2:
                raise ValidationError('Tags need to be filled with at least 2 values')
