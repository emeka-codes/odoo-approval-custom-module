from odoo import models, fields, api
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class PurchaseApprovalRequest(models.Model):
    _inherit = 'approval.request'


    approved_departments = fields.Many2many('hr.department', string="Approved Departments")

    def action_approve(self):
        """Allow one user per department to approve."""
        for rec in self:
            user = self.env.user
            # Find employee record for the current user
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            if not employee or not employee.department_id:
                raise UserError("You don't have a department assigned in your employee record.")

            user_department = employee.department_id

            # Check if someone from this department already approved
            if user_department in rec.approved_departments:
                raise UserError(f"The {user_department.name} department has already approved this request.")

            # Record that this department has approved
            rec.approved_departments = [(4, user_department.id)]

            # Log the action in the chatter
            rec.message_post(body=f"{user.name} from {user_department.name} department approved this request.")

            # Check if all departments (of approvers) have approved
            approvers = rec.approver_ids
            all_departments = self.env['hr.employee'].search([
                ('user_id', 'in', approvers.ids),
                ('department_id', '!=', False)
            ]).mapped('department_id')

            # Departments that have not yet approved
            remaining_departments = all_departments - rec.approved_departments

            if not remaining_departments:
                # All departments involved have approved
                rec.write({'request_status': 'approved'})
                rec.message_post(body="All departments have approved. Request fully approved.")
            else:
                next_dept_names = ', '.join(remaining_departments.mapped('name'))
                rec.message_post(body=f"Waiting for approval from: {next_dept_names}")



    def action_create_purchase_orders(self):
        result = super(PurchaseApprovalRequest, self).action_create_purchase_orders()

        purchase_orders = self.env['purchase.order']
        if isinstance(result, models.BaseModel):
            purchase_orders = result
        else:
            for approval in self:
                pos = self.env['purchase.order'].search([('origin', '=', approval.name)])
                purchase_orders |= pos

        for approval in self:
            _logger.info(f"🔎 Processing approval: {approval.name} ({approval.id}) model={approval._name}")

            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', approval._name),
                ('res_id', '=', approval.id)
            ])
            _logger.info(f"📎 Found {len(attachments)} attachment(s) for approval {approval.name}")

            if not attachments:
                continue

            if isinstance(result, models.BaseModel):
                pos_for_approval = purchase_orders.filtered(lambda p: p.origin == approval.name)
            else:
                pos_for_approval = self.env['purchase.order'].search([('origin', '=', approval.name)])

            _logger.info(f"🧾 Found {len(pos_for_approval)} purchase orders linked to approval {approval.name}")

            for po in pos_for_approval:
                for att in attachments:
                    new_att = att.copy({'res_model': 'purchase.order', 'res_id': po.id})
                    _logger.info(f"✅ Copied attachment {att.name} (ID: {att.id}) "
                                 f"to PO {po.name} (New attachment ID: {new_att.id})")

        return result
