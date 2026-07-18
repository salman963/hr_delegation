from odoo import models, fields, api, Command
from odoo.exceptions import ValidationError, UserError
from datetime import date


class HrDelegation(models.Model):
    _name = 'hr.delegation'
    _description = 'Manager Delegation'
    _rec_name = 'delegator_id'
    _order = 'date_from desc'

    delegator_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Delegator Manager',
        required=True,
        ondelete='cascade',
        help='The manager who is going on leave.',
    )
    delegatee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Delegatee Manager',
        required=True,
        ondelete='restrict',
        help='The manager who will cover responsibilities during the delegation period.',
    )
    delegator_user_id = fields.Many2one(
        comodel_name='res.users',
        related='delegator_id.user_id',
        store=True,
        string='Delegator User',
    )
    delegatee_user_id = fields.Many2one(
        comodel_name='res.users',
        related='delegatee_id.user_id',
        store=True,
        string='Delegatee User',
    )
    date_from = fields.Date(
        string='From',
        required=True,
    )
    date_to = fields.Date(
        string='To',
        required=True,
    )
    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('active', 'Active'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending',
        tracking=True,
        string='Status',
    )
    leave_id = fields.Many2one(
        comodel_name='hr.leave',
        string='Source Leave',
        readonly=True,
        ondelete='set null',
        help='The leave request that triggered this delegation.',
    )
    note = fields.Text(string='Notes')


    # ── Constraints ──────────────────────────────────────────────────────────

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self.filtered(lambda this: this.date_from and this.date_to):
            if rec.date_from > rec.date_to:
                raise ValidationError(
                    "End date must be on or after the start date."
                )
            if rec.date_from < date.today() and rec.date_to > date.today():
                rec.state = 'active'

    @api.constrains('delegator_id', 'delegatee_id')
    def _check_not_same(self):
        for rec in self:
            if rec.delegator_id == rec.delegatee_id:
                raise ValidationError(
                    "The delegating manager and the acting manager must be "
                    "different employees."
                )



    def _get_subordinates(self):
        """Return direct reports of the delegator."""
        self.ensure_one()
        return self.env['hr.employee'].search(['|',
                                ('parent_id', '=', self.delegator_id.id),
                                ('coach_id', '=', self.delegator_id.id)
        ])


    def update_user_access(self,grant_access=False, remove_access=False):
        delegator = self.delegator_user_id
        delegatee = self.delegatee_user_id
        if not (delegator.res_user_access and delegatee.res_user_access):
            raise UserError('The delegator user or delegatee user must have a user role.')
        delegator_role_groups = delegator.res_user_access.user_groups
        delegatee_role_groups = delegatee.res_user_access.user_groups
        delegator_extra_groups = delegator_role_groups - delegatee_role_groups

        delegator_extra_groups.write({'users': [(4, delegatee.id)] if grant_access else [(3, delegatee.id)]})

    def action_activate(self):
        """Set delegatee_parent_id on all subordinates of the delegator."""
        for rec in self:
            if rec.state != 'pending':
                continue
            subordinates = rec._get_subordinates()

            rec.update_user_access(grant_access=True)

            if subordinates:
                subordinates.write({
                    'delegations': [Command.link(rec.id)] # [(4,0,id)]
                })
            rec.state = 'active'
            template = self.env.ref('hr_delegation.mail_template_delegation_activated')
            template.send_mail(rec.id, force_send=True)

    def action_deactivate(self):
        """Clear delegatee_parent_id from subordinates when delegation ends."""
        for rec in self:
            if rec.state != 'active':
                continue
            subordinates = rec._get_subordinates()

            subordinates.write({'delegations': [Command.unlink(rec.id)]})  # [(3,0,id)]
            rec.state = 'done'
            rec.update_user_access(remove_access=True)
            template = self.env.ref('hr_delegation.mail_template_delegation_deactivated')
            template.send_mail(rec.id, force_send=True)

    def action_cancel(self):
        """Cancel the delegation, deactivating it first if already active."""
        for rec in self:
            if rec.state == 'active':
                rec.action_deactivate()
            if rec.state in ('pending', 'done'):
                rec.state = 'cancelled'

    # ── Scheduled action ──────────────────────────────────────────────────────

    @api.model
    def _cron_update_delegation_states(self):
        today = fields.Date.today()

        # Pending → Active
        to_activate = self.search([
            ('state', '=', 'pending'),
            ('date_from', '<=', today),
            ('date_to', '>=', today),
        ])
        to_activate.action_activate()

        # Active → Done
        to_close = self.search([
            ('state', '=', 'active'),
            ('date_to', '<', today),
        ])
        to_close.action_deactivate()
