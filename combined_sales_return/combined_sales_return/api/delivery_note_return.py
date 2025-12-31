# delivery_note_return.py

import frappe
from frappe.utils import nowdate


def create_return_delivery_note(
    *,
    original_delivery_note,
    items,
    combined_sales_return
):
    """
    Create Delivery Note Return against original Delivery Note
    """

    original_dn = frappe.get_doc(
        "Delivery Note",
        original_delivery_note
    )

    dn = frappe.get_doc({
        "doctype": "Delivery Note",
        "is_return": 1,
        "return_against": original_dn.name,   # ✅ MUST BE DN
        "company": original_dn.company,
        "customer": original_dn.customer,
        "posting_date": frappe.utils.nowdate(),
        "combined_sales_return": combined_sales_return,
        "items": []
    })

    for row in items:
        si_item = frappe.get_doc(
            "Sales Invoice Item",
            row.sales_invoice_item
        )

        # safety (should already be true)
        if not si_item.delivery_note or not si_item.dn_detail:
            continue

        dn.append("items", {
            "item_code": row.item_code,
            "qty": abs(row.qty),              # POSITIVE
            "uom": row.uom,
            "warehouse": si_item.warehouse,   # from original DN
            "delivery_note_item": si_item.dn_detail
        })

    # nothing to return → do nothing
    if not dn.items:
        return None

    dn.insert(ignore_permissions=True)
    dn.submit()

    return dn.name


