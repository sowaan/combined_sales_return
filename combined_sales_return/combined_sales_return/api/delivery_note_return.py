
import frappe 
# from frappe.utils import nowdate

import frappe
from frappe.utils import nowdate, flt


def create_return_delivery_note(original_delivery_note, items, combined_sales_return):

    original_dn = frappe.get_doc("Delivery Note", original_delivery_note)

    dn_return = frappe.new_doc("Delivery Note")
    dn_return.is_return = 1
    dn_return.naming_series = "MAT-DN-RET-.YYYY.-"
    dn_return.return_against = original_delivery_note
    dn_return.customer = original_dn.customer
    dn_return.company = original_dn.company
    dn_return.posting_date = frappe.utils.nowdate()
    # dn_return.territory = original_dn.territory

    for row in items:

        si_item = frappe.get_doc(
            "Sales Invoice Item",
            row.sales_invoice_item
        )

        if not si_item.delivery_note:
            continue

        dn_item_name = frappe.db.get_value(
            "Delivery Note Item",
            {
                "parent": si_item.delivery_note,
                "item_code": si_item.item_code
            },
            "name"
        )

        if not dn_item_name:
            continue

        dn_item = frappe.get_doc("Delivery Note Item", dn_item_name)

        #  Store Warehouse
        if row.store_qty and row.store_qty > 0:
            dn_return.append("items", {
                "item_code": row.item_code,
                "qty": -abs(row.store_qty),
                "warehouse": row.store_warehouse,

                # 🔑 THIS FIELD IS MANDATORY
                "delivery_note_item": dn_item.name,
                "territory": row.territory,
                "uom": row.uom,
                "rate": row.rate,
                "cost_center": dn_item.cost_center,
                "expense_account": dn_item.expense_account
            })

        #  Damage Warehouse
        if row.damage_qty and row.damage_qty > 0:
            dn_return.append("items", {
                "item_code": row.item_code,
                "qty": -abs(row.damage_qty),
                "warehouse": row.damage_warehouse,
                "uom": row.uom,
                # 🔑 THIS FIELD IS MANDATORY
                "delivery_note_item": dn_item.name,
                "territory": row.territory,
                "rate": row.rate,
                "cost_center": dn_item.cost_center,
                "expense_account": dn_item.expense_account
            })

    dn_return.insert(ignore_permissions=True)
    dn_return.submit()


@frappe.whitelist()
def get_customer_delivery_notes(txt, doctype, searchfield, start, page_len, filters):
    filters = frappe.parse_json(filters or {})

    customer = filters.get("customer")
    if not customer:
        return []

    #  Already returned Delivery Notes
    returned_dns = frappe.get_all(
        "Delivery Note",
        filters={
            "is_return": 1,
            "docstatus": 1
        },
        pluck="return_against"
    )

    # Valid Delivery Notes
    dns = frappe.get_all(
        "Delivery Note",
        filters={
            "customer": customer,
            "docstatus": 1,
            "is_return": 0,
            "name": ["like", f"%{txt}%"]
        },
        fields=["name"],
        start=start,
        page_length=page_len
    )

    #  Exclude already returned DN
    result = [
        [dn.name] for dn in dns
        if dn.name not in returned_dns
    ]

    return result
