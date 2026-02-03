# Copyright (c) 2026, Sowaan Pvt. Ltd and contributors
# For license information, please see license.txt

# import frappe
# from frappe.model.document import Document


# class CombinedDeliveryNoteReturn(Document):
# 	pass
# import frappe
# from frappe.model.document import Document

# class CombinedDeliveryNoteReturn(Document):
#     def on_submit(self):
#         self.create_delivery_note_returns()

#     def create_delivery_note_returns(self):
#         dn_map = {}

#         for row in self.items:
#             dn_map.setdefault(row.delivery_note, []).append(row)

#         for dn, items in dn_map.items():
#             return_dn = frappe.new_doc("Delivery Note")
#             return_dn.is_return = 1
#             return_dn.return_against = dn
#             return_dn.customer = self.customer
#             return_dn.company = self.company

#             for i in items:
#                 if i.store_qty:
#                     return_dn.append("items", {
#                         "item_code": i.item_code,
#                         "qty": i.store_qty,
#                         "warehouse": i.store_warehouse,
#                         "rate": i.rate
#                     })

#                 if i.damage_qty:
#                     return_dn.append("items", {
#                         "item_code": i.item_code,
#                         "qty": i.damage_qty,
#                         "warehouse": i.damage_warehouse,
#                         "rate": i.rate
#                     })

#             return_dn.insert(ignore_permissions=True)
#             return_dn.submit()


# @frappe.whitelist()
# def get_delivery_note_items(customer):
#     data = []

#     dns = frappe.get_all(
#         "Delivery Note",
#         filters={
#             "customer": customer,
#             "docstatus": 1
#         },
#         pluck="name"
#     )

#     for dn in dns:
#         items = frappe.get_all(
#             "Delivery Note Item",
#             filters={"parent": dn},
#             fields=["item_code", "item_name", "qty", "rate"]
#         )

#         for i in items:
#             data.append({
#                 "delivery_note": dn,
#                 "item_code": i.item_code,
#                 "item_name": i.item_name,
#                 "qty": i.qty,
#                 "rate": i.rate
#             })

#     return data


# import frappe
# from frappe.model.document import Document

# class CombinedDeliveryNoteReturn(Document):

#     def on_submit(self):
#         dn_map = {}

#         for row in self.items:
#             dn_map.setdefault(row.delivery_note, []).append(row)

#         for dn, rows in dn_map.items():
#             return_dn = frappe.new_doc("Delivery Note")
#             return_dn.is_return = 1
#             return_dn.return_against = dn
#             return_dn.customer = self.customer
#             return_dn.company = self.company

#             for r in rows:
#                 if r.store_qty:
#                     return_dn.append("items", {
#                         "item_code": r.item_code,
#                        "qty": -abs(r.store_qty),  
#                         "warehouse": r.store_warehouse,
#                         "rate": r.rate
#                     })
#                 if r.damage_qty:
#                     return_dn.append("items", {
#                         "item_code": r.item_code,
#                        "qty": -abs(r.damage_qty), 
#                         "warehouse": r.damage_warehouse,
#                         "rate": r.rate
#                     })

#             return_dn.insert(ignore_permissions=True)
#             return_dn.submit()


# @frappe.whitelist()
# def get_delivery_note_items(customer):
#     data = []

#     dns = frappe.get_all(
#         "Delivery Note",
#         filters={"customer": customer, "docstatus": 1},
#         pluck="name"
#     )

#     for dn in dns:
#         items = frappe.get_all(
#             "Delivery Note Item",
#             filters={"parent": dn},
#             fields=["item_code", "item_name", "qty", "rate"]
#         )

#         for i in items:
#             frappe.log_error("the item value is:", f"item: {i}")
#             data.append({
#                 "delivery_note": dn,
#                 "item_code": i.item_code,
#                 "item_name": i.item_name,
#                 "delivered_qty": i.qty,
#                 "return_qty": i.qty,
#                 "rate": i.rate
#             })

#     return data

# **********************++++****************************

# import frappe
# from frappe.model.document import Document

# class CombinedDeliveryNoteReturn(Document):

#     def on_submit(self):
#         dn_map = {}

#         # Step 1: group by Delivery Note
#         for row in self.items:
#             dn_map.setdefault(row.delivery_note, []).append(row)

#         # Step 2: process each Delivery Note
#         for dn, rows in dn_map.items():

#             original_dn = frappe.get_doc("Delivery Note", dn)

#             return_dn = frappe.new_doc("Delivery Note")
#             return_dn.is_return = 1
#             return_dn.return_against = dn
#             return_dn.customer = self.customer
#             return_dn.company = self.company
#             return_dn.posting_date = self.posting_date

#             for r in rows:

#                 # Step 3: find matching DN item row
#                 dn_item = next(
#                     (i for i in original_dn.items if i.item_code == r.item_code),
#                     None
#                 )

#                 if not dn_item:
#                     frappe.throw(
#                         f"Item {r.item_code} not found in Delivery Note {dn}"
#                     )

#                 # Step 4: Store Warehouse return
#                 if r.store_qty and r.store_qty > 0:
#                     return_dn.append("items", {
#                         "item_code": r.item_code,
#                         "qty": -abs(r.store_qty),
#                         "warehouse": r.store_warehouse,
#                         "rate": r.rate,
#                         "delivery_note_item": dn_item.name,
#                         "cost_center": dn_item.cost_center,
#                         "expense_account": dn_item.expense_account,
#                         "territory": dn_item.territory
#                     })

#                 # Step 5: Damage Warehouse return
#                 if r.damage_qty and r.damage_qty > 0:
#                     return_dn.append("items", {
#                         "item_code": r.item_code,
#                         "qty": -abs(r.damage_qty),
#                         "warehouse": r.damage_warehouse,
#                         "rate": r.rate,
#                         "delivery_note_item": dn_item.name,
#                         "cost_center": dn_item.cost_center,
#                         "expense_account": dn_item.expense_account,
#                         "territory": dn_item.territory
#                     })

#             return_dn.insert(ignore_permissions=True)
#             return_dn.submit()


# @frappe.whitelist()
# def get_delivery_note_items(customer):
#     data = []

#     dns = frappe.get_all(
#         "Delivery Note",
#         filters={"customer": customer, "docstatus": 1},
#         pluck="name"
#     )

#     for dn in dns:
#         items = frappe.get_all(
#             "Delivery Note Item",
#             filters={"parent": dn},
#             fields=[
#                 "name",
#                 "item_code",
#                 "item_name",
#                 "qty",
#                 "rate"
#             ]
#         )

#         for i in items:
#             data.append({
#                 "delivery_note": dn,
#                 "delivery_note_item": i.name,
#                 "item_code": i.item_code,
#                 "item_name": i.item_name,
#                 "delivered_qty": i.qty,
#                 "return_qty": i.qty,
#                 "rate": i.rate,
#                 "amount": i.qty * i.rate
#             })

#     return data




import frappe
from frappe.model.document import Document
from frappe.utils import flt


class CombinedDeliveryNoteReturn(Document):

    # """
    # DocType: Combined Delivery Note Return
    # """

    # def validate_return_quantities(self):
    #     for i, row in enumerate(self.items, start=1):

    #         if not row.delivery_note or not row.delivery_note_item:
    #             continue

    #         return_qty = abs(flt(row.delivered_qty or 0))

    #         # store + damage = total return
    #         current_qty = abs(
    #             flt(row.store_qty or 0) + flt(row.damage_qty or 0)
    #         )

    #         submitted_qty, draft_qty = get_dn_returned_qty_breakdown(
    #             row.delivery_note,
    #             row.delivery_note_item,
    #             exclude_docname=self.name
    #         )

    #         remaining = return_qty - submitted_qty

    #         # 🔒 HARD BLOCK
    #         if current_qty > remaining:
    #             frappe.throw(
    #                 f"""
    #                 <b>Row {i} – {row.item_code}</b><br>
    #                 Original Qty: {return_qty}<br>
    #                 Already Returned (Submitted): {submitted_qty}<br>
    #                 Remaining: {remaining}<br>
    #                 Attempted Return: {current_qty}
    #                 """,
    #                 title="Return Quantity Exceeded"
    #             )

    #         # ⚠️ SOFT WARNING
    #         if draft_qty > 0:
    #             frappe.msgprint(
    #                 f"""
    #                 <b>Notice – {row.item_code}</b><br>
    #                 Draft Delivery Note Returns exist
    #                 with quantity <b>{draft_qty}</b>.<br><br>
    #                 Validation is based on submitted returns only.
    #                 """,
    #                 indicator="orange",
    #                 alert=True
    #             )

    def on_submit(self):
        dn_map = {}

        # 1️⃣ Group by Delivery Note
        for row in self.items:
            if not row.delivery_note:
                continue
            dn_map.setdefault(row.delivery_note, []).append(row)

        # 2️⃣ Create DN Return per Delivery Note
        for dn, rows in dn_map.items():
            original_dn = frappe.get_doc("Delivery Note", dn)

            return_dn = frappe.new_doc("Delivery Note")
            return_dn.is_return = 1
            return_dn.naming_series = "MAT-DN-RET-.YYYY.-" 
            return_dn.return_against = dn
            return_dn.customer = self.customer
            return_dn.company = self.company
            return_dn.posting_date = self.posting_date

            for r in rows:
                # Match exact DN Item row
                # dn_item = next(
                #     (i for i in original_dn.items if i.name == r.delivery_note_item),
                #     None
                # )
                dn_item = next(
                    (i for i in original_dn.items if i.item_code == r.item_code),
                    None
                )

                if not dn_item:
                    frappe.throw(
                        f"Item {r.item_code} not found in Delivery Note {dn}"
                    )

                # 🏬 Store Qty
                if flt(r.store_qty) > 0:
                    return_dn.append("items", {
    "item_code": r.item_code,
    "qty": -abs(r.store_qty),
    "warehouse": r.store_warehouse,
    "rate": dn_item.rate,
    "territory": dn_item.territory,
    "uom": dn_item.uom,

    # 🔥 REQUIRED LINKING FIELDS
    "dn_detail": dn_item.name,
    "against_sales_invoice": dn_item.against_sales_invoice,
    "si_detail": dn_item.si_detail,

    "cost_center": dn_item.cost_center,
    "expense_account": dn_item.expense_account,
})

                # 💥 Damage Qty
                if flt(r.damage_qty) > 0:
                    return_dn.append("items", {
    "item_code": r.item_code,
    "qty": -abs(r.damage_qty),
    "warehouse": r.damage_warehouse,
    "rate": dn_item.rate,
    "territory": dn_item.territory,
    "uom": dn_item.uom,

    # 🔥 REQUIRED LINKING FIELDS
    "dn_detail": dn_item.name,
    "against_sales_invoice": dn_item.against_sales_invoice,
    "si_detail": dn_item.si_detail,

    "cost_center": dn_item.cost_center,
    "expense_account": dn_item.expense_account,
})
                    if flt(r.store_qty) + flt(r.damage_qty) > flt(r.return_qty):
                     frappe.throw( f"Return qty cannot exceed remaining qty for item {r.item_code}"
    )


            return_dn.insert(ignore_permissions=True)
            return_dn.submit()


# new code hain
# @frappe.whitelist()
# def get_delivery_note_items(customer, delivery_note=None, item_code=None, fetch_all=0):
#     fetch_all = int(fetch_all)

#     if not customer or not fetch_all:
#         return []

#     # 🔴 Already returned Delivery Notes
#     returned_dns = frappe.get_all(
#         "Delivery Note",
#         filters={
#             "is_return": 1,
#             "docstatus": 1
#         },
#         pluck="return_against"
#     )

#     dn_filters = {
#         "customer": customer,
#         "docstatus": 1,
#         "is_return": 0
#     }

#     if delivery_note:
#         dn_filters["name"] = delivery_note

#     dns = frappe.get_all(
#         "Delivery Note",
#         filters=dn_filters,
#         pluck="name"
#     )

#     data = []

#     for dn in dns:
#         # ❌ skip already returned DN
#         if dn in returned_dns:
#             continue

#         item_filters = {"parent": dn}

#         if item_code:
#             item_filters["item_code"] = item_code

#         items = frappe.get_all(
#             "Delivery Note Item",
#             filters=item_filters,
#             fields=[
#                 "name",
#                 "item_code",
#                 "item_name",
#                 "qty",
#                 "rate"
#             ]
#         )

#         for i in items:
#             data.append({
#                 "delivery_note": dn,
#                 "delivery_note_item": i.name,
#                 "item_code": i.item_code,
#                 "item_name": i.item_name,
#                 "delivered_qty": i.qty,
#                 "rate": i.rate,
#                 "amount": flt(i.qty) * flt(i.rate)
#             })

#     return data

# new code righte 

# @frappe.whitelist()
# def get_delivery_note_items(customer, delivery_note=None, item_code=None, fetch_all=0):
#     if not customer:
#         return []

#     # 🔴 Already returned Delivery Notes (Combined Return ban chuki)
#     returned_dns = frappe.get_all(
#         "Delivery Note",
#         filters={
#             "is_return": 1,
#             "docstatus": 1
#         },
#         pluck="return_against"
#     )

#     # 🔵 Base Delivery Note filters (tumhara original logic)
#     dn_filters = {
#         "customer": customer,
#         "docstatus": 1,
#         "is_return": 0
#     }

#     # ✅ Agar specific Delivery Note select ho
#     if delivery_note:
#         dn_filters["name"] = delivery_note

#     # 🔵 Original DN fetch (simple & working)
#     dns = frappe.get_all(
#         "Delivery Note",
#         filters=dn_filters,
#         pluck="name"
#     )

#     if not dns:
#         return []

#     # 🔴 Sales Invoice ban chuke Delivery Notes
#     invoiced_dns = frappe.db.sql("""
#         SELECT DISTINCT delivery_note
#         FROM `tabSales Invoice Item`
#         WHERE docstatus = 1
#           AND delivery_note IS NOT NULL
#     """, pluck="delivery_note")

#     data = []

#     for dn in dns:
#         # ❌ Agar DN already return ho chuka ya invoice ban chuki
#         if dn in returned_dns or dn in invoiced_dns:
#             continue

#         # 🔴 Sales Invoice ban chuke DN Items
#         invoiced_dn_items = frappe.get_all(
#             "Sales Invoice Item",
#             filters={
#                 "docstatus": 1,
#                 "delivery_note": dn
#             },
#             pluck="dn_detail"   # ✅ ERPNext v15 correct field
#         )

#         item_filters = {"parent": dn}

#         # ✅ Item filter (tumhara existing feature)
#         if item_code:
#             item_filters["item_code"] = item_code

#         items = frappe.get_all(
#             "Delivery Note Item",
#             filters=item_filters,
#             fields=[
#                 "name",
#                 "item_code",
#                 "item_name",
#                 "qty",
#                 "rate"
#             ]
#         )

#         for i in items:
#             # ❌ Agar specific item invoice ho chuka
#             if i.name in invoiced_dn_items:
#                 continue

#             data.append({
#                 "delivery_note": dn,
#                 "delivery_note_item": i.name,
#                 "item_code": i.item_code,
#                 "item_name": i.item_name,
#                 "delivered_qty": i.qty,
#                 "rate": i.rate,
#                 "amount": flt(i.qty) * flt(i.rate)
#             })

#     return data



# @frappe.whitelist()
# def get_delivery_note_items(customer, delivery_note=None, item_code=None, fetch_all=0):
#     if not customer:
#         return []
#     returned_dns = frappe.get_all(
#         "Delivery Note",
#         filters={
#             "is_return": 1,
#             "docstatus": 1
#         },
#         pluck="return_against"
#     )
#     # Base Delivery Note filters
#     dn_filters = {
#         "customer": customer,
#         "docstatus": 1,
#         "is_return": 0
#     }

#     if delivery_note:
#         dn_filters["name"] = delivery_note

#     # Get original Delivery Notes
#     dns = frappe.get_all(
#         "Delivery Note",
#         filters=dn_filters,
#         pluck="name"
#     )

#     if not dns:
#         return []
    

#     data = []

#     for dn in dns:
#         dn_doc = frappe.get_doc("Delivery Note", dn)

#         for i in dn_doc.items:

#             # Item filter (optional)
#             if item_code and i.item_code != item_code:
#                 continue

#             # 🔴 TOTAL RETURNED QTY (ERPNext v15 SAFE)
#             returned_qty = frappe.db.sql("""
#                 SELECT ABS(SUM(dni.qty))
#                 FROM `tabDelivery Note Item` dni
#                 INNER JOIN `tabDelivery Note` rdn
#                     ON rdn.name = dni.parent
#                 WHERE rdn.docstatus = 1
#                   AND rdn.is_return = 1
#                   AND rdn.return_against = %s
#                   AND dni.item_code = %s
#             """, (dn, i.item_code))[0][0] or 0

#             remaining_qty = flt(i.qty) - flt(returned_qty)

#             # ❌ Fully returned → don't show
#             if remaining_qty <= 0:
#                 continue

#             data.append({
#                 "delivery_note": dn,
#                 "delivery_note_item": i.name,
#                 "item_code": i.item_code,
#                 "item_name": i.item_name,
#                 "delivered_qty": remaining_qty,   # ✅ remaining qty
#                 "rate": i.rate,
#                 "amount": flt(remaining_qty) * flt(i.rate)
#             })

#     return data

import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_delivery_note_items(customer, delivery_note=None, item_code=None, fetch_all=0):
    if not customer:
        return []

    # 🔵 Base Delivery Note filters (only original DNs)
    dn_filters = {
        "customer": customer,
        "docstatus": 1,
        "is_return": 0
    }

    if delivery_note:
        dn_filters["name"] = delivery_note

    dns = frappe.get_all(
        "Delivery Note",
        filters=dn_filters,
        pluck="name"
    )

    if not dns:
        return []

    # 🔴 Fully invoiced Delivery Notes (hide completely)
    invoiced_dns = frappe.db.sql("""
        SELECT DISTINCT delivery_note
        FROM `tabSales Invoice Item`
        WHERE docstatus = 1
          AND delivery_note IS NOT NULL
    """, pluck="delivery_note")

    data = []

    for dn in dns:

        # ❌ DN fully invoiced → skip
        if dn in invoiced_dns:
            continue

        dn_doc = frappe.get_doc("Delivery Note", dn)

        # 🔴 Invoiced DN Items (partial invoice case)
        invoiced_dn_items = frappe.get_all(
            "Sales Invoice Item",
            filters={
                "docstatus": 1,
                "delivery_note": dn
            },
            pluck="dn_detail"
        )

        for i in dn_doc.items:

            # ❌ Item filter
            if item_code and i.item_code != item_code:
                continue

            # ❌ Item already invoiced
            if i.name in invoiced_dn_items:
                continue

            # 🔴 TOTAL RETURNED QTY (ERPNext v15 SAFE)
            returned_qty = frappe.db.sql("""
                SELECT ABS(SUM(dni.qty))
                FROM `tabDelivery Note Item` dni
                INNER JOIN `tabDelivery Note` rdn
                    ON rdn.name = dni.parent
                WHERE rdn.docstatus = 1
                  AND rdn.is_return = 1
                  AND rdn.return_against = %s
                  AND dni.item_code = %s
            """, (dn, i.item_code))[0][0] or 0

            remaining_qty = flt(i.qty) - flt(returned_qty)

            # ❌ Fully returned → hide
            if remaining_qty <= 0:
                continue

            data.append({
                "delivery_note": dn,
                "delivery_note_item": i.name,
                "item_code": i.item_code,
                "item_name": i.item_name,
                "uom": i.uom,    
                "delivered_qty": remaining_qty,   # ✅ remaining qty
                "rate": i.rate,
                "amount": flt(remaining_qty) * flt(i.rate)
            })

    return data
