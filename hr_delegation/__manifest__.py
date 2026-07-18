{
    'name': 'HR Manager Delegation',
    'version': '17.0.0.0',
    'category': 'Human Resources',
    'summary': 'Delegate manager responsibilities during leave periods',
    'description': """
        Allows a line manager going on leave to delegate their responsibilities
        to another manager for a defined period. Access rights and record rules
        are handled via the delegatee_parent_id field on hr.employee — no
        changes to the core parent_id / coach_id hierarchy.
    """,
    'author': 'Salman Malik',
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
