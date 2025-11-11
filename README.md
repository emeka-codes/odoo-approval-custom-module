# odoo-approval-custom-module
This is a odoo custom module i built, it is an extension of the base approval module.

# What problem does it solve?
1. This module solves the department by department approval issue in odoo
2. It also solves the transfer of attachments or documents from an RFQ request record to the corresponding RFQ created from that record.

By default, odoo only allows for individual approval flow, but there are common business scenarios whereby they might want either of the employee from a department to be able to approve a request then that request should move on to the next department to approve. 
Also, out of the box, any document attached to a particular RFQ request doesn't follow through to the corresponding RFQ that is being created from that record.

This custom module was built to solve these issues highlighted above.
