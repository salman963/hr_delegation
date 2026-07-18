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

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    delegatee_user_ids = fields.Many2many(
        'res.users',
        compute='_compute_delegatee_users',
        store=True,
        string='Delegatee Users',
    )

    delegations = fields.Many2many('hr.delegation',string='Delegations')

    @api.depends('delegations')
    def _compute_delegatee_users(self):
        for rec in self:
            rec.delegatee_user_ids = [(6,0,rec.delegations.mapped('delegatee_id').mapped('user_id').ids)]

