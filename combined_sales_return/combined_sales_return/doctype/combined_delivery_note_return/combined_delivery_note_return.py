# Copyright (c) 2026, Sowaan Pvt. Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class CombinedDeliveryNoteReturn(Document):

    def validate(self):
        self.validate_return_quantities()
        self.validate_warehouse_selection()
        self.validate_qty_breakup()

    def validate_qty_breakup(self):

        for i, row in enumerate(self.items, start=1):

            return_qty = flt(row.return_qty)
            store_qty = flt(row.store_qty)
            damage_qty = flt(row.damage_qty)

            if abs(return_qty) <= 0:
                continue

            if (store_qty + damage_qty) != return_qty:

                frappe.throw(
                    f"""
                    <b>Row {i} – {row.item_code}</b><br><br>
                    Store Qty ({store_qty}) + Damage Qty ({damage_qty})<br>
                    must be equal to Return Qty ({abs(return_qty)}).
                    """,
                    title="Quantity Mismatch"
                )

    def validate_return_quantities(self):

        for i, row in enumerate(self.items, start=1):

            if not row.delivery_note_item:
                continue

            # 1️⃣ Original delivered stock qty
            dn_item = frappe.get_doc(
                "Delivery Note Item",
                row.delivery_note_item
            )

            original_stock_qty = abs(flt(dn_item.stock_qty))

            frappe.msgprint(f"original_stock_qty {original_stock_qty}")

            # 2️⃣ Already submitted returns (other documents)
            submitted_stock_qty = frappe.db.sql("""
                SELECT ABS(SUM(dni.stock_qty))
                FROM `tabDelivery Note Item` dni
                INNER JOIN `tabDelivery Note` dn
                    ON dn.name = dni.parent
                WHERE dn.docstatus = 1
                AND dn.is_return = 1
                AND dn.return_against = %s
                AND dni.dn_detail = %s
            """, (
                row.delivery_note,
                row.delivery_note_item,
            ))[0][0] or 0

            # 3️⃣ Sum all rows of THIS document (stock UOM)
            current_doc_stock_qty = 0

            for r in self.items:

                if r.delivery_note_item == row.delivery_note_item:

                    if r.uom == dn_item.stock_uom:
                        conversion_factor = 1
                    else:
                        conversion_factor = flt(r.conversion_factor or 1)

                    current_doc_stock_qty += (
                        abs(flt(r.return_qty or 0)) * conversion_factor
                    )

            #frappe.msgprint(f"submitted_stock_qty {submitted_stock_qty} current_doc_stock_qty {current_doc_stock_qty}")

            total_after_this_return = submitted_stock_qty + current_doc_stock_qty

            # 4️⃣ Final validation
            if total_after_this_return > original_stock_qty:

                frappe.throw(
                    f"""
                    <b>Row {i} – {row.item_code}</b><br><br>
                    Original Delivered Qty: {original_stock_qty}<br>
                    Already Returned (Submitted): {submitted_stock_qty}<br>
                    This Document Total: {current_doc_stock_qty}<br>
                    <br>
                    <b>Total After Return: {total_after_this_return}</b><br><br>
                    Return quantity exceeds Delivery Note quantity.
                    """,
                    title="Return Quantity Exceeded"
                )


    def validate_warehouse_selection(self):

        for i, row in enumerate(self.items, start=1):

            # -------------------------------------------------
            # 1️⃣ Store Qty Validation
            # -------------------------------------------------
            if flt(row.store_qty) > 0 and not row.store_warehouse:
                frappe.throw(
                    f"""
                    <b>Row {i} – {row.item_code}</b><br><br>
                    Store Warehouse is missing.
                    """,
                    title="Missing Store Warehouse"
                )

            # -------------------------------------------------
            # 2️⃣ Damage Qty Validation
            # -------------------------------------------------
            if flt(row.damage_qty) > 0 and not row.damage_warehouse:
                frappe.throw(
                    f"""
                    <b>Row {i} – {row.item_code}</b><br><br>
                    Damage Warehouse is missing
                    """,
                    title="Missing Damage Warehouse"
                )

    

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
                        "expense_account": dn_item.expense_account,
                        "territory": dn_item.territory
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
                        "expense_account": dn_item.expense_account,
                        "territory": dn_item.territory
                    })

            # frappe.throw(
            #                 f"Test error just to stop submitt for debugging purposes. Remove this line after testing."
            #             )
            return_dn.insert(ignore_permissions=True)
            return_dn.submit()


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

            #frappe.msgprint(f"delivered_stock_qty {delivered_stock_qty}")

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

            # Calculate stock_uom_rate
            if i.conversion_factor:
                stock_uom_rate = flt(i.rate) / flt(i.conversion_factor)
            else:
                stock_uom_rate = i.rate

            #frappe.msgprint(f"i.conversion_factor {i.conversion_factor}")

            data.append({
                "delivery_note": dn,
                "delivery_note_item": i.name,
                "item_code": i.item_code,
                "item_name": i.item_name,

                "uom": i.uom,
                "remaining_stock_qty": remaining_stock_qty,

                "remaining_ctn": ctn,
                "remaining_pcs": pcs,

                "delivered_qty": ctn if ctn > 0 else pcs,

                "rate": i.rate,  # DN rate (CTN rate)
                "dn_rate": i.rate,   # explicit
                "stock_uom": i.stock_uom,
                "stock_uom_rate": stock_uom_rate,
                "conversion_factor": i.conversion_factor    
            })


    return data


