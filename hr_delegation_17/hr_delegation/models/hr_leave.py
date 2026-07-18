################################################################################
#
#    Copyright (C) 2026-TODAY Salman Malik
#
#    Author: Salman Malik
#    Email: salmanmalik9475@gmail.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License (LGPL-3)
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program. If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo import models, api,fields, _
from odoo.exceptions import UserError, AccessError


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    delegate_employee = fields.Many2one('hr.employee', string="Delegate Employee")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        return records

    def write(self, vals):
        res = super().write(vals)
        # Only re-sync when delegation-relevant fields change
        relevant = {'delegate_employee', 'request_date_from', 'request_date_to', 'state'}
        if relevant.intersection(vals.keys()):
            self._sync_delegation()
        return res

    @api.constrains('state')
    def _check_delegation(self):
        for rec in self:
            if rec.state == 'validate' and rec.delegate_employee:
                existing_delegation = rec.env['hr.delegation'].search([
                    ('leave_id', '=', self.id)
                ], limit=1)
                delegation_values = {'delegator_id': rec.employee_id.id,
                                'delegatee_id': rec.delegate_employee.id,
                                'date_from': rec.request_date_from,
                                'date_to': rec.request_date_to}
                if existing_delegation:
                    existing_delegation.write(delegation_values)
                else:
                    delegation_values.update({'leave_id': rec.id})

                    rec.env['hr.delegation'].create(delegation_values)


    def _get_employee_domain(self):
        domain = [
            ('active', '=', True),
            ('company_id', 'in', self.env.companies.ids),
        ]
        if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            domain += [
                '|','|',
                ('user_id', '=', self.env.uid),
                ('leave_manager_id', '=', self.env.uid),
                ('delegatee_user_ids', 'in', [self.env.uid])
            ]
        return domain

    # ── Sync logic ────────────────────────────────────────────────────────────

    def _sync_delegation(self):
        Delegation = self.env['hr.delegation']

        for leave in self:
            existing = Delegation.search([
                ('leave_id', '=', leave.id),
            ], limit=1)

            # If leave is cancel / reset to expired → cancel any delegation
            if leave.state in ('cancel', 'expired'):
                if existing and existing.state in ('pending', 'active'):
                    existing.action_cancel()
                continue

            # No delegation user set → nothing to do
            if not leave.delegate_employee:
                continue

            delegatee_employee = leave.delegate_employee

            vals = {
                'delegator_id': leave.employee_id.id,
                'delegatee_id': delegatee_employee.id,
                'date_from': leave.request_date_from,
                'date_to': leave.request_date_to,
            }

            if existing:
                existing.write(vals)


    def action_view_delegation(self):
        self.ensure_one()
        delegation = self.env['hr.delegation'].search([
            ('leave_id', '=', self.id)
        ], limit=1)
        # if not delegation:
        #     return
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.delegation',
            'res_id': delegation.id,
            'view_mode': 'form',
            'context':{'default_delegator_id':self.employee_id.id,'default_delegatee_id':self.delegate_employee.id,'default_date_from':self.request_date_from,
                       'default_date_to':self.request_date_to,'default_leave_id':self.id},
            'target': 'new',
        }

    @api.depends('state', 'employee_id', 'department_id')
    def _compute_can_approve(self):
        for holiday in self:
            try:
                h_state = holiday.state
                current_employee = self.env.user.employee_id
                h_employee = holiday.employee_id
                is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')
                is_manager = self.env.user.has_group('hr_holidays.group_hr_holidays_manager')
                if holiday.employee_id == current_employee \
                        and self.env.user != holiday.employee_id.leave_manager_id \
                        and not is_officer:
                    raise UserError(_('Only a Time Off Officer or Manager can approve/refuse its own requests.'))

                if h_state == 'confirm' and holiday.validation_type == 'both':
                    holiday._check_approval_update('validate1')
                elif h_state in ('confirm', 'pm_approve') and holiday.validation_type == 'nt_workflow':
                    if h_state == 'confirm':
                        line_manager = h_employee.parent_id.user_id
                        delegatee_user_ids = h_employee.delegatee_user_ids
                        if self.env.user == line_manager or (
                                self.env.user in delegatee_user_ids) or is_officer or is_manager:
                            holiday.can_approve = True
                        else:
                            raise UserError(
                                _('Only a Time Off Officer or Manager can approve/refuse its own requests.'))
                else:
                    holiday._check_approval_update('validate')
            except (AccessError, UserError):
                holiday.can_approve = False
            else:
                holiday.can_approve = True

    def get_leave_domain_from_xml(self, xmlid=None,all_keys=None):
        xml_values = {
            'hr_holidays.hr_leave_rule_responsible_read': """[
                                                                '|',
                                                                    ('employee_id.leave_manager_id', '=', user.id),
                                                                    ('employee_id.delegatee_user_ids', 'in', [user.id])
                                                            ]""",

            'hr_holidays.hr_leave_rule_officer_update': """[
                                                            ('holiday_type', '=', 'employee'),
                                                            '|',
                                                                '|',
                                                                    '&',
                                                                        ('employee_id.user_id', '=', user.id),
                                                                        ('state', '!=', 'validate'),
                                                                ('employee_id.leave_manager_id', '=', user.id),
                                                            ('employee_id.delegatee_user_ids', 'in', [user.id])
                                                        ]""",

            'hr_holidays.hr_leave_rule_responsible_update': """[
                                                                ('holiday_type', '=', 'employee'),
                                                                '|','|',
                                                                    '&',
                                                                        ('employee_id.user_id', '=', user.id),
                                                                        ('state', '!=', 'validate'),
                                                                    ('employee_id.leave_manager_id', '=', user.id),
                                                                    ('employee_id.delegatee_user_ids', 'in', [user.id]),
                                                            ]""",

            'hr_holidays.hr_leave_rule_employee_update': """[
                                                            ('holiday_type', '=', 'employee'),
                                                            '&',
                                                                '|',
                                                                    '&',
                                                                        ('employee_id.user_id', '=', user.id),
                                                                        ('state', 'not in', ['validate', 'validate1']),
                                                                    ('validation_type', 'in', ['manager', 'both', 'no_validation']),
                                                            '|',
                                                                ('employee_id.delegatee_user_ids', 'in', [user.id]),
                                                                ('employee_id.leave_manager_id', '=', user.id)
                                                        ]""",

            'hr_holidays.hr_leave_allocation_rule_employee': """[
                                                            '|','|',
                                                            ('employee_id.leave_manager_id', '=', user.id),
                                                            ('employee_id.delegatee_user_ids', 'in', [user.id]),
                                                            ('employee_id.user_id', '=', user.id),
                                                            ]""",
            'hr_holidays.hr_leave_allocation_rule_employee_update':"""[
                                                            ('holiday_status_id.requires_allocation', '=', 'yes'),
                                                            ('holiday_status_id.employee_requests', '=', 'yes'),
                                                            ('holiday_type', '=', 'employee'),
                                                            '|',
                                                            ('employee_id.user_id', '=', user.id),
                                                            '&',
                                                            ('validation_type', '=', 'officer'),
                                                            '|',
                                                             ('employee_id.delegatee_user_ids', 'in', [user.id]),
                                                             ('employee_id.leave_manager_id', '=', user.id),
                                                            ]"""

        }
        return xml_values.get(xmlid)

    @api.model
    def _update_rule(self, xmlid):
        rule = self.env.ref(xmlid)
        if domain := self.get_leave_domain_from_xml(xmlid):
            rule.sudo().write({
                'domain_force': domain,
            })
