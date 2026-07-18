from . import models
from odoo import  api


def get_leave_orignal_domain():
    xml_values = {
        'hr_holidays.hr_leave_rule_responsible_read': """[('employee_id.leave_manager_id', '=', user.id)]""",
        'hr_holidays.hr_leave_rule_officer_update': """[('holiday_type', '=', 'employee'),'|','&',('employee_id.user_id', '=', user.id),('state', '!=', 'validate'),'|',('employee_id.user_id', '!=', user.id),('employee_id.user_id', '=', False)]""",
        'hr_holidays.hr_leave_rule_responsible_update': """[('holiday_type', '=', 'employee'),'|','&',('employee_id.user_id', '=', user.id),('state', '!=', 'validate'),('employee_id.leave_manager_id', '=', user.id),]""",
        'hr_holidays.hr_leave_rule_employee_update': """[('holiday_type', '=', 'employee'),'|','&',('employee_id.user_id', '=', user.id),('state', 'not in', ['validate', 'validate1']),'&',('validation_type', 'in', ['manager', 'both', 'no_validation']),('employee_id.leave_manager_id', '=', user.id),]""",
        'hr_holidays.hr_leave_allocation_rule_employee': """['|',('employee_id.leave_manager_id', '=', user.id),('employee_id.user_id', '=', user.id),]""",
        'hr_holidays.hr_leave_allocation_rule_employee_update': """[('holiday_status_id.requires_allocation', '=', 'yes'),('holiday_status_id.employee_requests', '=', 'yes'),('holiday_type', '=', 'employee'),'|',('employee_id.user_id', '=', user.id),'&',('validation_type', '=', 'officer'),('employee_id.leave_manager_id', '=', user.id),]"""

    }
    return xml_values


def get_orignal_domain_force():
    domain_values = {}

    leave_orignal_domain = get_leave_orignal_domain()
    domain_values.update(leave_orignal_domain)
    return domain_values

def _uninstall_hook(env):
    all_key_values = get_orignal_domain_force()
    for key,value in all_key_values.items():
        rule_id = env.ref(key)
        rule_id.write({'domain_force': value})
