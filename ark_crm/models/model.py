from odoo import fields, models, api, SUPERUSER_ID
from odoo.exceptions import ValidationError
from logging import getLogger
from datetime import datetime, timedelta, date
import pytz
from dateutil import tz


_logger = getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    _order = "last_update_openchatter desc,priority desc,activity_date_deadline,id desc"

    active = fields.Boolean(track_visibility='onchange')

    @api.constrains('tag_ids')
    def constrains_tag_ids(self):
        for rec in self:
            if len(rec.tag_ids) < 2 or len(set(rec.tag_ids.mapped('color'))) < 2:
                raise ValidationError('Tags need to be filled with at least 2 diffrent values')

    @api.depends("write_date")
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
            _logger.info('update last_update_openchatter id crm.lead: %s' % (document.id))

    @api.multi
    def _compute_day_from_last_chatter(self):
        dt_now = datetime.now()
        for document in self:
            if document.last_update_openchatter:
                last_update_openchatter = datetime.strptime(document.last_update_openchatter, "%Y-%m-%d %H:%M:%S")
                day_from_last_chatter = abs((dt_now - last_update_openchatter).days)
            else:
                day_from_last_chatter = 0
            document.day_from_last_chatter = day_from_last_chatter
            # _logger.info('update day_from_last_chatter id crm.lead: %s' % (document.id))
            
    day_from_last_chatter = fields.Float(
        string="Day From Last Update Openchatter",
        compute="_compute_day_from_last_chatter"
    )


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    @api.multi
    def _auto_archieve(self):
        self.ensure_one()
        obj_crm_lead = self.env["crm.lead"]
        now_utc = datetime.now().astimezone(tz.gettz('UTC'))
        now_localize = now_utc.astimezone(tz.gettz(self.env.user.tz))
        for auto_archieve in self.stage_auto_archieve_ids:
            date_day_limit_openchatter = now_localize + timedelta(days=-(auto_archieve.day_limit_openchatter))
            date_day_limit_openchatter = date_day_limit_openchatter.astimezone(tz.gettz('UTC'))
            date_day_limit_openchatter = date_day_limit_openchatter.strftime("%Y-%m-%d %H:%M:%S")
            criteria = [
                ("stage_id", "=", auto_archieve.stage_id.id),
                ("active", "=", True),
                '|', ("day_on_stage", ">", auto_archieve.day_limit),
                ("last_update_openchatter", "<", date_day_limit_openchatter),
            ]
            leads = obj_crm_lead.search(criteria)
            if leads:
                for lead in leads:
                    lead.write({"active": False})


class CRMStageAutoArchieve(models.Model):
    _inherit = "crm.stage_auto_archieve"

    day_limit_openchatter = fields.Float(
        string="Day Limit Openchatter", default=60
    )