# Copyright (c) 2025, Sowaan Pvt. Ltd
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint
from frappe.utils import flt, money_in_words
from combined_sales_return.combined_sales_return.api.delivery_note_return import create_return_delivery_note
class CombinedSalesReturn(Document):
    """
    DocType: Combined Sales Return
    """

    def validate(self):        

        self.validate_return_quantities()
        
        self.calculate_totals()

        self.validate_qty_breakup()

    def validate_return_quantities(self):

        # --------------------------------------------
        # 1️⃣ Group rows by Sales Invoice Item
        # --------------------------------------------
        grouped = {}

        for row in self.combined_sales_return_items:

            if not row.sales_invoice_item:
                continue

            grouped.setdefault(row.sales_invoice_item, []).append(row)

        # --------------------------------------------
        # 2️⃣ Validate each invoice item group
        # --------------------------------------------
        for invoice_item, rows in grouped.items():

            # Fetch original invoice item
            si_item = frappe.get_doc("Sales Invoice Item", invoice_item)

            frappe.msgprint(f"si_item.parent {si_item.parent} invoice_item {invoice_item}")

            original_stock_qty = abs(flt(si_item.stock_qty))

            # ----------------------------------------
            # 3️⃣ Calculate current document stock qty
            # ----------------------------------------
            current_doc_stock_qty = 0

            for row in rows:

                conversion_factor = flt(row.conversion_factor) or 1
                qty = abs(flt(row.qty))

                current_doc_stock_qty += qty * conversion_factor

            # ----------------------------------------
            # 4️⃣ Get already submitted returns
            # ----------------------------------------
            submitted_stock_qty, draft_qty = get_returned_qty_breakdown(
                si_item.parent,
                invoice_item,
                exclude_docname=self.name
            )

            total_after_this_return = submitted_stock_qty + current_doc_stock_qty

            # ----------------------------------------
            # 5️⃣ Final Validation
            # ----------------------------------------
            if total_after_this_return > original_stock_qty:
                #return
                frappe.throw(
                    f"""
                    <b>Item: {si_item.item_code}</b><br><br>
                    Original Invoice Stock Qty: {original_stock_qty}<br>
                    Already Returned (Submitted): {submitted_stock_qty}<br>
                    Current Document (Stock): {current_doc_stock_qty}<br>
                    <br>
                    <b>Total After Return: {total_after_this_return}</b><br><br>
                    Return quantity exceeds Sales Invoice quantity.
                    """,
                    title="Return Quantity Exceeded"
                )

            # ----------------------------------------
            # 6️⃣ Prevent fractional stock qty
            # ----------------------------------------
            if not float(current_doc_stock_qty).is_integer():

                frappe.throw(
                    f"""
                    <b>Item: {si_item.item_code}</b><br><br>
                    Stock quantity must be a whole number.<br>
                    Calculated stock qty: {current_doc_stock_qty}
                    """,
                    title="Invalid Stock Quantity"
                )


    def validate_qty_breakup(self):

        for i, row in enumerate(self.combined_sales_return_items, start=1):

            return_qty = flt(row.qty)   # In Sales Return it's usually `qty`
            store_qty = flt(row.store_qty)
            damage_qty = flt(row.damage_qty)

            #frappe.msgprint (f"return_qty {return_qty} store_qty {store_qty} damage_qty {damage_qty}")

            if abs(return_qty) <= 0:
                #frappe.msgprint(f"total_Quantity {total_Quantity}")
                frappe.throw(
                    f"""                    
                    Return quantity can not be ({abs(return_qty)}).
                    """,
                    title="Invalid Quantity"
                )
            
            total_Quantity = store_qty + damage_qty;

            if abs(total_Quantity) <= 0:
                frappe.throw(
                    f"""
                    <b>Row {i} – {row.item_code}</b><br><br>
                    Store Qty ({store_qty}) + Damage Qty ({damage_qty})<br>
                    can not be 0.
                    """,
                    title="Quantity Mismatch"
                )

            if abs(total_Quantity) != abs(return_qty):
                #frappe.msgprint(f"total_Quantity {total_Quantity}")
                frappe.throw(
                    f"""
                    <b>Row {i} – {row.item_code}</b><br><br>
                    Store Qty ({store_qty}) + Damage Qty ({damage_qty})<br>
                    must be equal to Return Qty ({abs(return_qty)}).
                    """,
                    title="Quantity Mismatch"
                )

                
    def on_submit(self):
        """
        CASE 2:
        - Multiple Invoices
        - Multiple Delivery Notes
        Creates:
        1. Credit Notes (Sales Invoice Return)
        2. Delivery Note Returns (Stock)
        """

        # -----------------------------
        # 1️⃣ CREATE CREDIT NOTES
        # -----------------------------
        create_credit_notes(
            self.name,
            submit_credit_notes=True
        )

        # -----------------------------
        # 2️⃣ GROUP BY DELIVERY NOTE
        # -----------------------------
        grouped_by_dn = {}

        for row in self.combined_sales_return_items:
            if not row.sales_invoice_item:
                continue

            si_item = frappe.get_doc("Sales Invoice Item", row.sales_invoice_item)

            if not si_item.delivery_note:
                continue

            grouped_by_dn.setdefault(
                si_item.delivery_note, []
            ).append(row)

        # -----------------------------
        # 3️⃣ CREATE DN RETURNS
        # -----------------------------
        for dn, items in grouped_by_dn.items():
            create_return_delivery_note(
                original_delivery_note=dn,
                items=items,
                combined_sales_return=self.name
            )

    def calculate_totals(self):
        total_qty = 0
        total_net_amount = 0
        total_taxes = 0


        for row in self.combined_sales_return_items:
            total_qty += abs(flt(row.qty or 0))
            total_net_amount += flt(row.rate * row.qty or 0)        # ✅ NET ONLY
            total_taxes += flt(row.vat_amount or 0)          # ✅ TAX ONLY

        self.total_qty = total_qty
        self.total = total_net_amount                        # NET
        self.total_taxes = total_taxes                       # TAX
        self.grand_total = flt(total_net_amount + total_taxes, 0)   # ✅ CORRECT

        # ✅ GRAND TOTAL IN WORDS (SAR)

        words = money_in_words(
        abs(self.grand_total),
        "SAR")

        #frappe.msgprint(f"words {words}")

        self.in_words = words
    
    
# ----------------------------------------------------------------------
# VAT HELPERS
# ----------------------------------------------------------------------

def get_invoice_vat_rate(invoice_name):
    """
    Fetch VAT rate (%) from Sales Taxes and Charges table
    Handles VAT coming from Taxes & Charges Template
    """
    taxes = frappe.get_all(
        "Sales Taxes and Charges",
        filters={
            "parent": invoice_name,
            "parenttype": "Sales Invoice",
            "docstatus": 1
        },
        fields=["rate", "account_head"]
    )

    for tax in taxes:
        # match VAT account safely
        if tax.account_head and "VAT" in tax.account_head.upper():
            return float(tax.rate or 0)

    return 0.0


# ----------------------------------------------------------------------
# FETCH SALES INVOICE ITEMS (WITH VAT SUPPORT)
# ----------------------------------------------------------------------

@frappe.whitelist()
def amount_in_words(amount):   
    amount = flt(amount)  
    words = money_in_words(
        abs(amount),
        "SAR")

    #frappe.msgprint(f"words {words}")

    return words


@frappe.whitelist()
def get_sales_invoice_items(customer=None, sales_invoice=None, select_all=0, item_code=None):
    """
    Fetch Sales Invoice Items and attach VAT info from Taxes table
    """
    if not customer:
        frappe.throw("Customer is required.")

    select_all = cint(select_all)

    sql = """
    SELECT
        sii.parent AS sales_invoice,
        sii.name AS invoice_item_row,
        si.posting_date AS sales_invoice_date,
        sii.item_code,
        sii.item_name,
        sii.description,
        sii.qty,
        sii.rate,
        sii.amount,
        sii.uom,
        sii.stock_qty,
        sii.stock_uom,
        sii.conversion_factor,
        sii.stock_uom_rate,
        sii.territory AS territory
    FROM `tabSales Invoice Item` sii
    INNER JOIN `tabSales Invoice` si ON sii.parent = si.name
    WHERE
        si.docstatus = 1
        AND si.is_return = 0


    """

    params = {"customer": customer}

    # Case 1: Item filter is applied → search ALL invoices of customer
    if item_code:
        sql += " AND si.customer = %(customer)s"

    # Case 2: Explicitly fetch all invoices
    elif select_all:
        sql += " AND si.customer = %(customer)s"

    # Case 3: Specific invoice selected
    else:
        if not sales_invoice:
            return []
        sql += " AND si.name = %(sales_invoice)s"
        params["sales_invoice"] = sales_invoice

    
    # ----------------------------------------
    # Item filter (ALWAYS by item_code)
    # ----------------------------------------
    if item_code:
        sql += " AND sii.item_code = %(item_code)s"
        params["item_code"] = item_code
        sql += " ORDER BY si.posting_date DESC"

    rows = frappe.db.sql(sql, params, as_dict=True)

    #frappe.msgprint(f"Rows {rows}")

    # ----------------------------------------------------------
    # Attach VAT rate & VAT amount PER ITEM (derived correctly)
    # ----------------------------------------------------------
    invoice_vat_cache = {}

    for r in rows:
        inv = r.sales_invoice

        if inv not in invoice_vat_cache:
            vat_rate = get_invoice_vat_rate(inv)
            invoice_vat_cache[inv] = vat_rate
        else:
            vat_rate = invoice_vat_cache[inv]

        vat_ratio = vat_rate / 100 if vat_rate else 0

        line_amount = (r.qty or 0) * (r.rate or 0)
        vat_amount = line_amount * vat_ratio

        r["uom"] = r.uom 
        r["vat_rate_ratio"] = vat_ratio
        r["vat_amount"] = vat_amount
        r["original_qty"] = r.qty
        r["max_returnable_qty"] = abs(r.qty or 0)
        r["original_stock_qty"] = abs(flt(r.stock_qty or 0))
        r["stock_uom"] = r.stock_uom
        r["conversion_factor"] = (flt(r.stock_qty) / flt(r.qty) if flt(r.qty) else 1)
        r["stock_uom_rate"] = flt(r.stock_uom_rate or r.rate)


    return rows

@frappe.whitelist()
def create_credit_notes(docname, submit_credit_notes=False):

    doc = frappe.get_doc("Combined Sales Return", docname)

    # Force validation before proceeding
    doc.validate_return_quantities()
    doc.validate_qty_breakup()

    grouped = {}
    for row in doc.combined_sales_return_items:
        if row.linked_invoice:
            grouped.setdefault(row.linked_invoice, []).append(row)

    messages = []

    for invoice, items in grouped.items():

        original_si = frappe.get_doc("Sales Invoice", invoice)

        cn = frappe.get_doc({
            "doctype": "Sales Invoice",
            "naming_series": "ACC-SINV-RET-.YYYY.-",
            "company": original_si.company,
            "customer": original_si.customer,
            "is_return": 1,
            "return_against": original_si.name,
            "posting_date": frappe.utils.nowdate(),
            "taxes_and_charges": original_si.taxes_and_charges,
            "territory": original_si.territory,
            "items": [],
            "taxes": []
        })

        # ---------------- ITEMS ----------------
        for item in items:

            si_item = frappe.get_doc(
                "Sales Invoice Item",
                item.sales_invoice_item
            )

            qty = item.qty if item.qty < 0 else -abs(item.qty)

            rate = item.rate
            if item.uom == si_item.stock_uom:
                rate = flt(si_item.stock_uom_rate)

            cn.append("items", {
                "item_code": item.item_code,
                "qty": qty,
                "rate": rate,
                "uom": item.uom,
                "sales_invoice_item": item.sales_invoice_item,
                "territory": item.territory
            })

        # ---------------- TAXES ----------------
        for tax in original_si.taxes:
            cn.append("taxes", {
                "charge_type": tax.charge_type,
                "account_head": tax.account_head,
                "description": tax.description,
                "rate": tax.rate,
                "included_in_print_rate": tax.included_in_print_rate,
                "cost_center": tax.cost_center,
                "territory": original_si.territory
            })

        # ---------------- FINALIZE ----------------
        cn.set_missing_values()
        cn.calculate_taxes_and_totals()
        cn.insert(ignore_permissions=True)

        if submit_credit_notes:
            cn.submit()

        messages.append(f"Credit Note created: {cn.name}")

    return "\n".join(messages)

def get_already_returned_qty(invoice, invoice_item_row):
    """
    Sum of already returned quantity for a specific
    Sales Invoice Item (submitted returns only)
    """

    #frappe.msgprint(f"invoice {invoice} invoice_item_row {invoice_item_row}")

    result = frappe.db.sql("""
        SELECT
            ABS(SUM(sii.qty))
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON sii.parent = si.name
        WHERE
            si.is_return = 1
            AND si.docstatus = 1
            AND si.return_against = %s
            AND sii.sales_invoice_item = %s
    """, (invoice, invoice_item_row))

    return flt(result[0][0]) if result and result[0][0] else 0


def get_returned_qty_breakdown(invoice, invoice_item_row, exclude_docname=None):
    """
    Returns (submitted_stock_qty, draft_stock_qty)
    All quantities are in STOCK UOM
    """
    frappe.msgprint(f"invoice {invoice} invoice_item_row {invoice_item_row}")

    params = [invoice, invoice_item_row]
    exclude_cond = ""

    if exclude_docname:
        exclude_cond = " AND si.name != %s"
        params.append(exclude_docname)

    rows = frappe.db.sql(f"""
        SELECT
            si.docstatus,
            ABS(SUM(sii.stock_qty)) AS stock_qty
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        WHERE
            si.is_return = 1
            AND si.return_against = %s
            AND sii.sales_invoice_item = %s
            {exclude_cond}
        GROUP BY si.docstatus
    """, params, as_dict=True)

    submitted = 0
    draft = 0

    for r in rows:
        if r.docstatus == 1:
            submitted = flt(r.stock_qty)
        elif r.docstatus == 0:
            draft = flt(r.stock_qty)

    return submitted, draft


@frappe.whitelist()
def get_conversion_factor(item_code, uom):
    """
    Securely fetch conversion factor from Item master
    """
    if not item_code or not uom:
        return None

    item = frappe.get_doc("Item", item_code)

    # frappe.msgprint(f"item {item}")
    # frappe.msgprint(f"uom selected {uom}")

    for d in item.uoms:
        if d.uom == uom:
            #frappe.msgprint(f"uom after {uom}")
            return flt(d.conversion_factor)

    return None



# ***********




