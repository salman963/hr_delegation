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

{
    'name': 'HR Manager Delegation',
    'version': '17.0.0.0',
    'author': 'Salman Malik',
    'category': 'Human Resources',
    'summary': 'Delegate manager responsibilities during leave periods',
    'description': """
        Allows a line manager going on leave to delegate their responsibilities
        to another manager for a defined period. Access rights and record rules
        are handled via the delegatee_parent_id field on hr.employee — no
        changes to the core parent_id / coach_id hierarchy.
    """,
    
    'depends': ['hr','hr_holidays','insys_user_access'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_delegation_security.xml',
        'security/leave_security.xml',
        'data/hr_delegation_cron.xml',
        'data/mail_template.xml',
        'views/hr_delegation_views.xml',
        'views/hr_leave_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',

    'uninstall_hook': '_uninstall_hook'
}
