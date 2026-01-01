# Copyright (c) 2025, abdopcnet@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class StampTaxCalculationRules(Document):
    pass


@frappe.whitelist()
def update_medico_trade_rules():
    """
    Update Stamp Tax Calculation Rules for Medico Trade
    Based on image: ats_tax_amount = 10.00, check_stamp_amount = 10.00 for range 1001-5000
    """
    try:
        # Get the document
        rules_doc = frappe.get_doc(
            "Stamp Tax Calculation Rules", "Medico Trade")

        # Update based on image: ats_tax_amount = 10.00, check_stamp_amount = 10.00 for range 1001-5000
        updated = False
        for range_row in rules_doc.stamp_tax_range:
            if flt(range_row.from_amount) == 1001 and flt(range_row.to_amount) == 5000:
                range_row.ats_tax_amount = 10.00
                range_row.check_stamp_amount = 10.00
                updated = True

        if updated:
            rules_doc.save(ignore_permissions=True)
            frappe.db.commit()
            return {
                "status": "success",
                "message": "Stamp Tax Calculation Rules updated successfully for range 1001-5000"
            }
        else:
            return {
                "status": "error",
                "message": "Range 1001-5000 not found"
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(),
                         "Error updating Stamp Tax Rules")
        return {
            "status": "error",
            "message": str(e)
        }
