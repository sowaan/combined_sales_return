# Copyright (c) 2026, Sowaan Pvt. Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class CombinedDeliveryNoteReturn(Document):

    def on_submit(self):
        dn_map = {}

        # Group by Delivery Note
        for row in self.items:
            if not row.delivery_note:
                continue
            dn_map.setdefault(row.delivery_note, []).append(row)

        #  Create DN Return per Delivery Note
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
                
                if flt(r.return_qty)> flt(dn_item.qty):
                    frappe.throw(
                        f"Return qty cannot exceed original qty for item {r.item_code}"
                    )
                # Store Qty
                if flt(r.store_qty) > 0:
                    return_dn.append("items", {
                        "item_code": r.item_code,
                        "qty": -abs(r.store_qty),
                        "warehouse": r.store_warehouse,
                        "rate": dn_item.rate,
                        "territory": dn_item.territory,
                        "uom": r.uom,
                        

                        #  REQUIRED LINKING FIELDS
                        "dn_detail": dn_item.name,
                        "against_sales_invoice": dn_item.against_sales_invoice,
                        "si_detail": dn_item.si_detail,

                        "cost_center": dn_item.cost_center,
                        "expense_account": dn_item.expense_account,
                    })

                #  Damage Qty
                if flt(r.damage_qty) > 0:
                    return_dn.append("items", {
                        "item_code": r.item_code,
                        "qty": -abs(r.damage_qty),
                        "warehouse": r.damage_warehouse,
                        "rate": dn_item.rate,
                        "territory": dn_item.territory,
                        "uom": r.uom,
                        #  REQUIRED LINKING FIELDS
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

    #  Fully invoiced Delivery Notes (hide completely)
    invoiced_dns = frappe.db.sql("""
        SELECT DISTINCT delivery_note
        FROM `tabSales Invoice Item`
        WHERE docstatus = 1
          AND delivery_note IS NOT NULL
    """, pluck="delivery_note")

    data = []

    for dn in dns:

        # DN fully invoiced → skip
        if dn in invoiced_dns:
            continue

        dn_doc = frappe.get_doc("Delivery Note", dn)

        #  Invoiced DN Items (partial invoice case)
        invoiced_dn_items = frappe.get_all(
            "Sales Invoice Item",
            filters={
                "docstatus": 1,
                "delivery_note": dn
            },
            pluck="dn_detail"
        )

        for i in dn_doc.items:

            #  Item filter
            if item_code and i.item_code != item_code:
                continue

            #  Item already invoiced
            if i.name in invoiced_dn_items:
                continue

            #  TOTAL RETURNED QTY (ERPNext v15 SAFE)
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

            #  Fully returned → hide
            if remaining_qty <= 0:
                continue

            data.append({
                "delivery_note": dn,
                "delivery_note_item": i.name,
                "item_code": i.item_code,
                "item_name": i.item_name,
                "uom": i.uom,    
                "delivered_qty": remaining_qty,  
                "rate": i.rate,
                "amount": flt(remaining_qty) * flt(i.rate)
            })

    return data
