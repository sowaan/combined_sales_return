// Copyright (c) 2026, Sowaan Pvt. Ltd and contributors
// For license information, please see license.txt


frappe.ui.form.on("Combined Delivery Note Return", {
    refresh(frm) {
           //  Remove auto-added empty row
        if (frm.is_new()) {
            frm.clear_table("items");
            frm.refresh_field("items");
        }
        frm.add_custom_button("Get Delivery Note Items", () => {
            if (!frm.doc.customer) {
                frappe.msgprint("Please select Customer first");
                return;
            }
            open_dn_popup(frm);
        });
    }
});

function open_dn_popup(frm) {
    let dialog = new frappe.ui.Dialog({
        title: "Select Delivery Note Items",
        size: "large",
        fields: [
            { fieldtype: "Section Break", label: "Filters" },

            {
                fieldname: "customer",
                fieldtype: "Link",
                label: "Customer",
                options: "Customer",
                default: frm.doc.customer,
                read_only: 1
            },
            { fieldtype: "Column Break" },

            // {
            //     fieldname: "delivery_note",
            //     fieldtype: "Link",
            //     label: "Delivery Note",
            //     options: "Delivery Note"
            // }
{
    fieldname: "delivery_note",
    fieldtype: "Link",
    label: "Delivery Note",
    options: "Delivery Note",
    get_query() {
        return {
            filters: {
                customer: dialog.get_value("customer"),
                docstatus: 1,
                is_return: 0
            }
        };
    }
}

            ,

            { fieldtype: "Section Break" },

            {
                fieldname: "item_code",
                fieldtype: "Link",
                label: "Item",
                options: "Item"
            },
            { fieldtype: "Column Break" },

            {
                fieldname: "fetch_all",
                fieldtype: "Check",
                label: "Fetch All Items",
                default: 0
            },

            { fieldtype: "Section Break", label: "Items" },
            { fieldname: "items_html", fieldtype: "HTML" }
        ],

        primary_action_label: "Add Selected Items",
        primary_action() {
            const $checked = dialog.$wrapper.find(".dn-item-check:checked");

            if (!$checked.length) {
                frappe.msgprint("Please select at least one item");
                return;
            }

            $checked.each(function () {
                let d = $(this).data();

                let row = frm.add_child("items");
                row.delivery_note = d.deliveryNote;
                row.delivery_note_item = d.dnItem;
                row.item_code = d.itemCode;
                row.item_name = d.itemName;
                row.uom = d.uom;
                row.delivered_qty = d.qty;
                row.return_qty = Math.abs(d.qty);
                row.rate = d.rate;
                row.amount = d.amount;
            });

            frm.refresh_field("items");
            dialog.hide();
        }
    });

    // ["delivery_note", "item_code", "fetch_all"].forEach(f => {
    //     dialog.fields_dict[f].df.onchange = () => load_dn_items(dialog);
    // });
    // Delivery Note & Item → normal reload
["delivery_note", "item_code"].forEach(f => {
    dialog.fields_dict[f].df.onchange = () => load_dn_items(dialog);
});

// Fetch All → clear filters + reload
dialog.fields_dict.fetch_all.df.onchange = () => {
    if (dialog.get_value("fetch_all")) {
        //  Clear Delivery Note & Item
        dialog.set_value("delivery_note", "");
        dialog.set_value("item_code", "");
    }
    load_dn_items(dialog);
};


    dialog.show();
    load_dn_items(dialog);
}


function load_dn_items(dialog) {
    const customer = dialog.get_value("customer");
    const delivery_note = dialog.get_value("delivery_note");
    const item_code = dialog.get_value("item_code");
    const fetch_all = dialog.get_value("fetch_all");

    // customer mandatory
    if (!customer) {
        dialog.fields_dict.items_html.set_value("<p>Please select Customer</p>");
        return;
    }

    //  nothing selected & fetch_all unchecked
    if (!delivery_note && !item_code && !fetch_all) {
        dialog.fields_dict.items_html.set_value(
            "<p>Please select <b>Delivery Note</b>, <b>Item</b> or check <b>Fetch All Items</b></p>"
        );
        return;
    }

    frappe.call({
        method: "combined_sales_return.combined_sales_return.doctype.combined_delivery_note_return.combined_delivery_note_return.get_delivery_note_items",
        args: {
            customer: customer,
            delivery_note: delivery_note,
            item_code: item_code,
            fetch_all: fetch_all ? 1 : 0
        },
        callback(r) {
            let rows = r.message || [];

            if (!rows.length) {
                dialog.fields_dict.items_html.set_value("<p>No items found</p>");
                return;
            }

            let html = `
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th></th>
                            <th>Delivery Note</th>
                            <th>Item</th>
                            <th>Qty</th>
                            <th>Rate</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            rows.forEach(r => {
                html += `
                    <tr>
                        <td>
                            <input type="checkbox" class="dn-item-check"
                                data-delivery-note="${r.delivery_note}"
                                data-dn-item="${r.delivery_note_item}"
                                data-item-code="${r.item_code}"
                                data-item-name="${r.item_name}"
                                data-qty="${r.delivered_qty}"
                                data-rate="${r.rate}"
                                data-uom="${r.uom}"  
                                data-amount="${r.amount}">
                        </td>
                        <td>${r.delivery_note}</td>
                        <td>${r.item_code} – ${r.item_name}</td>
                        <td>${r.delivered_qty}</td>
                        <td>${r.rate}</td>
                    </tr>`;
            });

            html += "</tbody></table>";
            dialog.fields_dict.items_html.set_value(html);
        }
    });
}


// Qty validation
frappe.ui.form.on("Combined Delivery Note Return Item", {
    store_qty(frm, cdt, cdn) { validate_qty(cdt, cdn); },
    damage_qty(frm, cdt, cdn) { validate_qty(cdt, cdn); }
});

function validate_qty(cdt, cdn) {
    let r = locals[cdt][cdn];
    let total = (r.store_qty || 0) + (r.damage_qty || 0);

    if (total !== r.return_qty) {
        frappe.show_alert({
            message: "Store Qty + Damage Qty must equal Return Qty",
            indicator: "orange"
        });
    }
}
