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

