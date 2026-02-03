# # delivery_note_return.py

# import frappe
# from frappe.utils import nowdate


# def create_return_delivery_note(
#     *,
#     original_delivery_note,
#     items,
#     combined_sales_return
# ):
#     """
#     Create Delivery Note Return against original Delivery Note
#     """

#     original_dn = frappe.get_doc(
#         "Delivery Note",
#         original_delivery_note
#     )

#     dn = frappe.get_doc({
#         "doctype": "Delivery Note",
#         "is_return": 1,
#         "return_against": original_dn.name,   # ✅ MUST BE DN
#         "company": original_dn.company,
#         "customer": original_dn.customer,
#         "posting_date": frappe.utils.nowdate(),
#         "combined_sales_return": combined_sales_return,
#         "items": []
#     })

#     for row in items:
#         si_item = frappe.get_doc(
#             "Sales Invoice Item",
#             row.sales_invoice_item
#         )

#         # safety (should already be true)
#         if not si_item.delivery_note or not si_item.dn_detail:
#             continue

#         dn.append("items", {
#             "item_code": row.item_code,
#             "qty": abs(row.qty),              # POSITIVE
#             "uom": row.uom,
#             "warehouse": si_item.warehouse,   # from original DN
#             "delivery_note_item": si_item.dn_detail
#         })

#     # nothing to return → do nothing
#     if not dn.items:
#         return None

#     dn.insert(ignore_permissions=True)
#     dn.submit()

#     return dn.name


# def create_return_delivery_note(original_delivery_note, items, combined_sales_return):

#     original_dn = frappe.get_doc("Delivery Note", original_delivery_note)

#     dn_return = frappe.new_doc("Delivery Note")
#     dn_return.is_return = 1
#     dn_return.return_against = original_delivery_note
#     dn_return.customer = original_dn.customer
#     dn_return.company = original_dn.company

#     for row in items:
#         dn_item = next(
#             (i for i in original_dn.items if i.item_code == row.item_code),
#             None
#         )

#         if not dn_item:
#             continue

#         if row.store_qty:
#             dn_return.append("items", {
#                 "item_code": row.item_code,
#                 "qty": -abs(row.store_qty),
#                 "warehouse": row.store_warehouse,
#                 "delivery_note_item": dn_item.name,
#                 "rate": row.rate,
#                 "territory": row.territory,
#                 "cost_center": dn_item.cost_center,
#                 "expense_account": dn_item.expense_account
#             })

#         if row.damage_qty:
#             dn_return.append("items", {
#                 "item_code": row.item_code,
#                 "qty": -abs(row.damage_qty),
#                 "warehouse": row.damage_warehouse,
#                 "delivery_note_item": dn_item.name,
#                 "rate": row.rate,
#                 "territory": row.territory,
#                 "cost_center": dn_item.cost_center,
#                 "expense_account": dn_item.expense_account
#             })

#     dn_return.insert(ignore_permissions=True)
#     dn_return.submit()


import frappe 
# from frappe.utils import nowdate

import frappe
from frappe.utils import nowdate, flt

# def create_return_delivery_note(original_delivery_note, items, combined_sales_return):
#     original_dn = frappe.get_doc("Delivery Note", original_delivery_note)

#     dn_return = frappe.new_doc("Delivery Note")
#     dn_return.is_return = 1
#     dn_return.return_against = original_delivery_note
#     dn_return.customer = original_dn.customer
#     dn_return.company = original_dn.company
#     dn_return.posting_date = nowdate()

#     for row in items:
#         if not row.sales_invoice_item:
#             continue

#         # 🔑 fetch Sales Invoice Item
#         si_item = frappe.get_doc("Sales Invoice Item", row.sales_invoice_item)

#         # 🔑 MUST exist to update DN qty correctly
#         if not si_item.delivery_note_item:
#             continue

#         dn_item = frappe.get_doc(
#             "Delivery Note Item",
#             si_item.delivery_note_item
#         )

#         # ---------------- STORE QTY ----------------
#         if flt(row.store_qty) > 0:
#             dn_return.append("items", {
#                 "item_code": row.item_code,
#                 "qty": -abs(row.store_qty),
#                 "warehouse": row.store_warehouse,
#                 "delivery_note_item": dn_item.name,  # ⭐ KEY LINE
#                 "rate": row.rate,
#                 "uom": row.uom,
#                 "cost_center": dn_item.cost_center,
#                 "expense_account": dn_item.expense_account
#             })

#         # ---------------- DAMAGE QTY ----------------
#         if flt(row.damage_qty) > 0:
#             dn_return.append("items", {
#                 "item_code": row.item_code,
#                 "qty": -abs(row.damage_qty),
#                 "warehouse": row.damage_warehouse,
#                 "delivery_note_item": dn_item.name,  # ⭐ KEY LINE
#                 "rate": row.rate,
#                 "uom": row.uom,
#                 "cost_center": dn_item.cost_center,
#                 "expense_account": dn_item.expense_account
#             })

#     dn_return.insert(ignore_permissions=True)
#     dn_return.submit()

#     return dn_return.name

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

        # 🏬 Store Warehouse
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

        # 💥 Damage Warehouse
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

    # 🔴 Already returned Delivery Notes
    returned_dns = frappe.get_all(
        "Delivery Note",
        filters={
            "is_return": 1,
            "docstatus": 1
        },
        pluck="return_against"
    )

    # 🟢 Valid Delivery Notes
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

    # ❌ Exclude already returned DN
    result = [
        [dn.name] for dn in dns
        if dn.name not in returned_dns
    ]

    return result
