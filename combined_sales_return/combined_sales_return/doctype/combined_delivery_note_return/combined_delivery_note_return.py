# Copyright (c) 2026, Sowaan Pvt. Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


# class CombinedDeliveryNoteReturn(Document):

#     def on_submit(self):
#         dn_map = {}

#         # 1️⃣ Group by Delivery Note
#         for row in self.items:
#             if not row.delivery_note:
#                 continue
#             dn_map.setdefault(row.delivery_note, []).append(row)

#         #  Create DN Return per Delivery Note
#         for dn, rows in dn_map.items():
#             original_dn = frappe.get_doc("Delivery Note", dn)

#             return_dn = frappe.new_doc("Delivery Note")
#             return_dn.is_return = 1
#             return_dn.naming_series = "MAT-DN-RET-.YYYY.-" 
#             return_dn.return_against = dn
#             return_dn.customer = self.customer
#             return_dn.company = self.company
#             return_dn.posting_date = self.posting_date

#             for r in rows:
#                 # Match exact DN Item row
#                 # dn_item = next(
#                 #     (i for i in original_dn.items if i.name == r.delivery_note_item),
#                 #     None
#                 # )
#                 dn_item = next(
#                     (i for i in original_dn.items if i.item_code == r.item_code),
#                     None
#                 )

#                 if not dn_item:
#                     frappe.throw(
#                         f"Item {r.item_code} not found in Delivery Note {dn}"
#                     )
                
#                 # if flt(r.return_qty)> flt(dn_item.qty):
#                 #     frappe.throw(
#                 #         f"Return qty cannot exceed original qty for item {r.item_code}"
#                 #     )
#                 # Store Qty
#                 if flt(r.store_qty) > 0:
#                     return_dn.append("items", {
#                         "item_code": r.item_code,
#                         "qty": -abs(r.store_qty),
#                         "warehouse": r.store_warehouse,
#                         "rate": dn_item.rate,
#                         "territory": dn_item.territory,
#                         "uom": r.uom,
                        

#                         #  REQUIRED LINKING FIELDS
#                         "dn_detail": dn_item.name,
#                         "against_sales_invoice": dn_item.against_sales_invoice,
#                         "si_detail": dn_item.si_detail,

#                         "cost_center": dn_item.cost_center,
#                         "expense_account": dn_item.expense_account,
#                     })

#                 #  Damage Qty
#                 if flt(r.damage_qty) > 0:
#                     return_dn.append("items", {
#                         "item_code": r.item_code,
#                         "qty": -abs(r.damage_qty),
#                         "warehouse": r.damage_warehouse,
#                         "rate": dn_item.rate,
#                         "territory": dn_item.territory,
#                         "uom": r.uom,
#                         #  REQUIRED LINKING FIELDS
#                         "dn_detail": dn_item.name,
#                         "against_sales_invoice": dn_item.against_sales_invoice,
#                         "si_detail": dn_item.si_detail,

#                         "cost_center": dn_item.cost_center,
#                         "expense_account": dn_item.expense_account,
#                     })
#                     if flt(r.store_qty) + flt(r.damage_qty) > flt(r.return_qty):
#                      frappe.throw( f"Return qty cannot exceed remaining qty for item {r.item_code}"
#     )


#             return_dn.insert(ignore_permissions=True)
#             return_dn.submit()

class CombinedDeliveryNoteReturn(Document):


    def on_submit(self):
        dn_map = {}

        for row in self.items:
            dn_map.setdefault(row.delivery_note, []).append(row)

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
                dn_item = next(
                    (i for i in original_dn.items if i.item_code == r.item_code),
                    None
                )

                if not dn_item:
                    frappe.throw(f"Item {r.item_code} not found in Delivery Note {dn}")

                # --------------------------------------------------
                # 1️⃣ Decimal block (business rule)
                # --------------------------------------------------
                for f in ["return_qty", "store_qty", "damage_qty"]:
                    if flt(getattr(r, f)) % 1 != 0:
                        frappe.throw(
                            f"Decimal quantity not allowed for item {r.item_code}"
                        )

                # --------------------------------------------------
                # 2️⃣ Delivered qty in STOCK UOM
                # --------------------------------------------------
                delivered_stock_qty = flt(dn_item.stock_qty)

                # --------------------------------------------------
                # 3️⃣ Already returned qty (STOCK UOM)
                # --------------------------------------------------
                already_returned = frappe.db.sql("""
                    SELECT ABS(SUM(dni.stock_qty))
                    FROM `tabDelivery Note Item` dni
                    INNER JOIN `tabDelivery Note` dn
                        ON dn.name = dni.parent
                    WHERE dn.is_return = 1
                      AND dn.docstatus = 1
                      AND dn.return_against = %s
                      AND dni.item_code = %s
                """, (dn, r.item_code))[0][0] or 0

                # --------------------------------------------------
                # 4️⃣ Current return qty → convert to STOCK UOM
                # --------------------------------------------------
                total_return_qty = flt(r.store_qty) + flt(r.damage_qty)

                if r.uom == dn_item.stock_uom:
                    current_return_stock_qty = total_return_qty
                else:
                    # CTN → PCS (or any UOM → stock_uom)
                    current_return_stock_qty = (
                        total_return_qty * flt(dn_item.conversion_factor)
                    )

                # --------------------------------------------------
                # 5️⃣ BALANCE CHECK
                # --------------------------------------------------
                balance_qty = (
                    delivered_stock_qty
                    - flt(already_returned)
                    - flt(current_return_stock_qty)
                )

                if balance_qty < 0:
                    frappe.throw(
                        f"Return quantity exceeds delivered quantity for item "
                        f"{r.item_code}. "
                        f"Remaining balance: "
                        f"{delivered_stock_qty - flt(already_returned)} "
                        f"{dn_item.stock_uom}"
                    )

                # --------------------------------------------------
                # 6️⃣ Rate logic (already correct)
                # --------------------------------------------------
                rate = dn_item.rate
                if r.uom == dn_item.stock_uom:
                    rate = dn_item.stock_uom_rate

                # --------------------------------------------------
                # 7️⃣ Append STORE
                # --------------------------------------------------
                if flt(r.store_qty) > 0:
                    return_dn.append("items", {
                        "item_code": r.item_code,
                        "qty": -abs(r.store_qty),
                        "warehouse": r.store_warehouse,
                        "uom": r.uom,
                        "rate": rate,
                        "dn_detail": dn_item.name,
                        "cost_center": dn_item.cost_center,
                        "expense_account": dn_item.expense_account
                    })

                # --------------------------------------------------
                # 8️⃣ Append DAMAGE
                # --------------------------------------------------
                if flt(r.damage_qty) > 0:
                    return_dn.append("items", {
                        "item_code": r.item_code,
                        "qty": -abs(r.damage_qty),
                        "warehouse": r.damage_warehouse,
                        "uom": r.uom,
                        "rate": rate,
                        "dn_detail": dn_item.name,
                        "cost_center": dn_item.cost_center,
                        "expense_account": dn_item.expense_account
                    })

            # frappe.throw(
            #                 f"Test error just to stop submitt for debugging purposes. Remove this line after testing."
            #             )
            return_dn.insert(ignore_permissions=True)
            return_dn.submit()


import frappe
from frappe.utils import flt

@frappe.whitelist()
def get_delivery_note_items(customer, delivery_note=None, item_code=None, fetch_all=0):
    if not customer:
        return []

    dn_filters = {
        "customer": customer,
        "docstatus": 1,
        "is_return": 0
    }

    if delivery_note:
        dn_filters["name"] = delivery_note

    dns = frappe.get_all("Delivery Note", filters=dn_filters, pluck="name")
    if not dns:
        return []

    invoiced_dns = frappe.db.sql("""
        SELECT DISTINCT delivery_note
        FROM `tabSales Invoice Item`
        WHERE docstatus = 1
          AND delivery_note IS NOT NULL
    """, pluck="delivery_note")

    data = []

    for dn in dns:
        if dn in invoiced_dns:
            continue

        dn_doc = frappe.get_doc("Delivery Note", dn)

        invoiced_dn_items = frappe.get_all(
            "Sales Invoice Item",
            filters={"docstatus": 1, "delivery_note": dn},
            pluck="dn_detail"
        )

        for i in dn_doc.items:

            if item_code and i.item_code != item_code:
                continue

            if i.name in invoiced_dn_items:
                continue

            # 1️⃣ Delivered & Returned in STOCK UOM
            delivered_stock_qty = flt(i.stock_qty)

            returned_stock_qty = frappe.db.sql("""
                SELECT ABS(SUM(dni.stock_qty))
                FROM `tabDelivery Note Item` dni
                INNER JOIN `tabDelivery Note` dn
                    ON dn.name = dni.parent
                WHERE dn.docstatus = 1
                  AND dn.is_return = 1
                  AND dn.return_against = %s
                  AND dni.item_code = %s
            """, (dn, i.item_code))[0][0] or 0

            remaining_stock_qty = delivered_stock_qty - returned_stock_qty

            if remaining_stock_qty <= 0:
                continue

            # 2️⃣ Split into CTN + PCS
            if i.uom != i.stock_uom:
                ctn = int(remaining_stock_qty // i.conversion_factor)
                pcs = int(remaining_stock_qty % i.conversion_factor)
            else:
                ctn = 0
                pcs = int(remaining_stock_qty)

            data.append({
                "delivery_note": dn,
                "delivery_note_item": i.name,
                "item_code": i.item_code,
                "item_name": i.item_name,

                # DN UOM (CTN)
                "uom": i.uom,

                # for calculations (still safe)
                "remaining_stock_qty": remaining_stock_qty,

                # 🔥 USER FRIENDLY
                "remaining_ctn": ctn,
                "remaining_pcs": pcs,

                # for backward compatibility
                "delivered_qty": ctn if ctn > 0 else pcs,

                "rate": i.rate,
                "stock_uom": i.stock_uom,
                "conversion_factor": i.conversion_factor
            })

    return data




# @frappe.whitelist()
# def get_delivery_note_items(customer, delivery_note=None, item_code=None, fetch_all=0):
#     if not customer:
#         return []

#     dn_filters = {
#         "customer": customer,
#         "docstatus": 1,
#         "is_return": 0
#     }

#     if delivery_note:
#         dn_filters["name"] = delivery_note

#     dns = frappe.get_all("Delivery Note", filters=dn_filters, pluck="name")
#     if not dns:
#         return []

#     invoiced_dns = frappe.db.sql("""
#         SELECT DISTINCT delivery_note
#         FROM `tabSales Invoice Item`
#         WHERE docstatus = 1
#           AND delivery_note IS NOT NULL
#     """, pluck="delivery_note")

#     data = []

#     for dn in dns:
#         if dn in invoiced_dns:
#             continue

#         dn_doc = frappe.get_doc("Delivery Note", dn)

#         invoiced_dn_items = frappe.get_all(
#             "Sales Invoice Item",
#             filters={
#                 "docstatus": 1,
#                 "delivery_note": dn
#             },
#             pluck="dn_detail"
#         )

#         for i in dn_doc.items:

#             if item_code and i.item_code != item_code:
#                 continue

#             if i.name in invoiced_dn_items:
#                 continue

#             # -------------------------------
#             # 1️⃣ Delivered qty in STOCK UOM
#             # -------------------------------
#             delivered_stock_qty = flt(i.stock_qty)

#             # -------------------------------
#             # 2️⃣ Returned qty in STOCK UOM
#             # -------------------------------
#             returned_stock_qty = frappe.db.sql("""
#                 SELECT ABS(SUM(dni.stock_qty))
#                 FROM `tabDelivery Note Item` dni
#                 INNER JOIN `tabDelivery Note` dn
#                     ON dn.name = dni.parent
#                 WHERE dn.docstatus = 1
#                   AND dn.is_return = 1
#                   AND dn.return_against = %s
#                   AND dni.item_code = %s
#             """, (dn, i.item_code))[0][0] or 0

#             remaining_stock_qty = delivered_stock_qty - flt(returned_stock_qty)

#             if remaining_stock_qty <= 0:
#                 continue

#             # ------------------------------------
#             # 3️⃣ Convert back to DN UOM for UI
#             # ------------------------------------
#             if i.uom == i.stock_uom:
#                 remaining_qty = remaining_stock_qty
#             else:
#                 remaining_qty = remaining_stock_qty / flt(i.conversion_factor)

#             # remaining_qty = remaining_stock_qty
            
#             data.append({
#                 "delivery_note": dn,
#                 "delivery_note_item": i.name,
#                 "item_code": i.item_code,
#                 "item_name": i.item_name,
#                 "uom": i.uom,                       # DN UOM
#                 "delivered_qty": remaining_qty,     # ✅ CORRECT BALANCE
#                 "rate": i.rate,
#                 "amount": flt(remaining_qty) * flt(i.rate)
#             })

#     return data

