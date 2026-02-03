// Copyright (c) 2026, Sowaan Pvt. Ltd and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Combined Delivery Note Return", {
// 	refresh(frm) {

// 	},
// });






/////**********//////
// frappe.ui.form.on("Combined Delivery Note Return", {
//     refresh(frm) {
//         frm.add_custom_button(
//             __("Get Delivery Note Items"),
//             () => {
//                 if (!frm.doc.customer) {
//                     frappe.msgprint("Please select Customer first");
//                     return;
//                 }
//                 get_delivery_note_items(frm);
//             }
//         );
//     }
// });

// function get_delivery_note_items(frm) {
//     frappe.call({
//         method: "combined_sales_return.combined_sales_return.doctype.combined_delivery_note_return.combined_delivery_note_return.get_delivery_note_items",
//         args: {
//             customer: frm.doc.customer
//         },
//         callback(r) {
//             if (r.message) {
//                 frm.clear_table("items");
//                 r.message.forEach(row => {
//                     let child = frm.add_child("items");
//                     child.delivery_note = row.delivery_note;
//                     child.item_code = row.item_code;
//                     child.item_name = row.item_name;
//                     child.delivered_qty = row.qty;
//                     child.rate = row.rate;
//                 });
//                 frm.refresh_field("items");
//             }
//         }
//     });
// }

// frappe.ui.form.on("Combined Delivery Note Return Item", {
//     store_qty(frm, cdt, cdn) {
//         validate_qty(frm, cdt, cdn);
//     },
//     damage_qty(frm, cdt, cdn) {
//         validate_qty(frm, cdt, cdn);
//     },
//     return_qty(frm, cdt, cdn) {
//         validate_qty(frm, cdt, cdn);
//     }
// });

// function validate_qty(frm, cdt, cdn) {
//     let row = locals[cdt][cdn];
//     let total = (row.store_qty || 0) + (row.damage_qty || 0);

//     if (row.return_qty && total > row.return_qty) {
//         frappe.throw("Store + Damage Qty return qty se zyada nahi ho sakti");
//     }
// }


///***// ///*/

// frappe.ui.form.on("Combined Delivery Note Return", {
//     refresh(frm) {
//         frm.add_custom_button("Get Delivery Note Items", () => {
//             if (!frm.doc.customer) {
//                 frappe.msgprint("Please select Customer first");
//                 return;
//             }

//             frappe.call({
//                 method: "combined_sales_return.combined_sales_return.doctype.combined_delivery_note_return.combined_delivery_note_return.get_delivery_note_items",
//                 args: { customer: frm.doc.customer },
//                 callback(r) {
//                     if (r.message) {
//                         frm.clear_table("items");
//                         r.message.forEach(d => {
//                             let row = frm.add_child("items");
//                             Object.assign(row, d);
//                         });
//                         frm.refresh_field("items");
//                     }
//                 }
//             });
//         });
//     }
// });

// frappe.ui.form.on("Combined Delivery Note Return Item", {
//     store_qty(frm, cdt, cdn) { validate_qty(cdt, cdn); },
//     damage_qty(frm, cdt, cdn) { validate_qty(cdt, cdn); }
// });

// function validate_qty(cdt, cdn) {
//     let r = locals[cdt][cdn];
//     let total = (r.store_qty || 0) + (r.damage_qty || 0);

//     if (total !== r.return_qty) {
//         frappe.show_alert("Store Qty + Damage Qty must equal Return Qty");
//         // frappe.throw("Store Qty + Damage Qty must equal Return Qty");
//     }
// }


// **************************************+++++*****************

// frappe.ui.form.on("Combined Delivery Note Return", {
//     refresh(frm) {
//         frm.add_custom_button("Get Delivery Note Items", () => {
//             if (!frm.doc.customer) {
//                 frappe.msgprint("Please select Customer first");
//                 return;
//             }
//             open_dn_item_popup(frm);
//         });
//     }
// });

// function open_dn_item_popup(frm) {
//     frappe.call({
//         method: "combined_sales_return.combined_sales_return.doctype.combined_delivery_note_return.combined_delivery_note_return.get_delivery_note_items",
//         args: {
//             customer: frm.doc.customer
//         },
//         callback(r) {
//             if (!r.message || !r.message.length) {
//                 frappe.msgprint("No Delivery Note Items found");
//                 return;
//             }

//             let dialog = new frappe.ui.Dialog({
//                 title: "Select Delivery Note Items",
//                 size: "extra-large",
//                 fields: [
//                     {
//                         fieldname: "items",
//                         fieldtype: "Table",
//                         label: "Delivery Note Items",
//                         cannot_add_rows: true,
//                         in_place_edit: false,
//                         fields: [
//                             {
//                                 fieldtype: "Check",
//                                 fieldname: "select",
//                                 label: "Select",
//                                 in_list_view: 1
//                             },
//                             {
//                                 fieldtype: "Data",
//                                 fieldname: "delivery_note",
//                                 label: "Delivery Note",
//                                 read_only: 1,
//                                 in_list_view: 1
//                             },
//                             {
//                                 fieldtype: "Data",
//                                 fieldname: "item_code",
//                                 label: "Item Code",
//                                 read_only: 1,
//                                 in_list_view: 1
//                             },
//                             {
//                                 fieldtype: "Data",
//                                 fieldname: "item_name",
//                                 label: "Item Name",
//                                 read_only: 1,
//                                 in_list_view: 1
//                             },
//                             {
//                                 fieldtype: "Float",
//                                 fieldname: "delivered_qty",
//                                 label: "Delivered Qty",
//                                 read_only: 1,
//                                 in_list_view: 1
//                             },
//                             {
//                                 fieldtype: "Currency",
//                                 fieldname: "rate",
//                                 label: "Rate",
//                                 read_only: 1,
//                                 in_list_view: 1
//                             }
//                         ],
//                         data: r.message
//                     }
//                 ],
//                 primary_action_label: "Add Selected Items",
//                 primary_action(values) {
//                     let selected = values.items.filter(row => row.select);

//                     if (!selected.length) {
//                         frappe.msgprint("Please select at least one item");
//                         return;
//                     }

//                     selected.forEach(row => {
//                         let child = frm.add_child("items");
//                         child.delivery_note = row.delivery_note;
//                         child.delivery_note_item = row.delivery_note_item;
//                         child.item_code = row.item_code;
//                         child.item_name = row.item_name;
//                         child.delivered_qty = row.delivered_qty;
//                         child.return_qty = row.delivered_qty;
//                         child.rate = row.rate;
//                         child.store_warehouse = row.store_warehouse;
//                         child.damage_warehouse = row.damage_warehouse;
//                         child.amount = row.amount;
                        
//                     });

//                     frm.refresh_field("items");
//                     dialog.hide();
//                 }
//             });

//             dialog.show();
//         }
//     });
// }

// // qty validation (same as before)
// frappe.ui.form.on("Combined Delivery Note Return Item", {
//     store_qty(frm, cdt, cdn) { validate_qty(cdt, cdn); },
//     damage_qty(frm, cdt, cdn) { validate_qty(cdt, cdn); }
// });

// function validate_qty(cdt, cdn) {
//     let r = locals[cdt][cdn];
//     let total = (r.store_qty || 0) + (r.damage_qty || 0);

//     if (total !== r.return_qty) {
//         frappe.show_alert({
//             message: "Store Qty + Damage Qty must equal Return Qty",
//             indicator: "orange"
//         });
//     }
// }

// ***************+++***************

frappe.ui.form.on("Combined Delivery Note Return", {
    refresh(frm) {
           // ✅ Remove auto-added empty row
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
        // ✅ Clear Delivery Note & Item
        dialog.set_value("delivery_note", "");
        dialog.set_value("item_code", "");
    }
    load_dn_items(dialog);
};


    dialog.show();
    load_dn_items(dialog);
}

// function load_dn_items(dialog) {
//     frappe.call({
//         method: "combined_sales_return.combined_sales_return.doctype.combined_delivery_note_return.combined_delivery_note_return.get_delivery_note_items",
//         args: {
//             customer: dialog.get_value("customer"),
//             delivery_note: dialog.get_value("delivery_note"),
//             item_code: dialog.get_value("item_code"),
//             fetch_all: dialog.get_value("fetch_all") ? 1 : 0
//         },
//         callback(r) {
//             let rows = r.message || [];

//             if (!rows.length) {
//                 dialog.fields_dict.items_html.set_value("<p>No items found</p>");
//                 return;
//             }

//             let html = `
//                 <table class="table table-bordered">
//                     <thead>
//                         <tr>
//                             <th></th>
//                             <th>Delivery Note</th>
//                             <th>Item</th>
//                             <th>Qty</th>
//                              <th>Rate</th>
                            
                        

//                         </tr>
//                     </thead><tbody>
//             `;

//             rows.forEach(r => {
//                 html += `
//                     <tr>
//                         <td>
//                             <input type="checkbox" class="dn-item-check"
//                                 data-delivery-note="${r.delivery_note}"
//                                 data-dn-item="${r.delivery_note_item}"
//                                 data-item-code="${r.item_code}"
//                                 data-item-name="${r.item_name}"
//                                 data-qty="${r.delivered_qty}"
//                                 data-rate="${r.rate}"
//                                 data-amount="${r.amount}">
//                         </td>
//                         <td>${r.delivery_note}</td>
//                         <td>${r.item_code} – ${r.item_name}</td>
//                         <td>${r.delivered_qty}</td>
//                         <td>${r.rate}</td>
                        
//                     </tr>`;
//             });

//             html += "</tbody></table>";
//             dialog.fields_dict.items_html.set_value(html);
//         }
//     });
// }

// new code hain already done
// function load_dn_items(dialog) {
//     // ✅ Fetch All unchecked → kuch bhi load na ho
//     if (!dialog.get_value("fetch_all")) {
//         dialog.fields_dict.items_html.set_value(
//             "<p>Please check <b>Fetch All Items</b> to load items</p>"
//         );
//         return;
//     }

//     frappe.call({
//         method: "combined_sales_return.combined_sales_return.doctype.combined_delivery_note_return.combined_delivery_note_return.get_delivery_note_items",
//         args: {
//             customer: dialog.get_value("customer"),
//             delivery_note: dialog.get_value("delivery_note"),
//             item_code: dialog.get_value("item_code"),
//             fetch_all: 1
//         },
//         callback(r) {
//             let rows = r.message || [];

//             if (!rows.length) {
//                 dialog.fields_dict.items_html.set_value("<p>No items found</p>");
//                 return;
//             }

//             let html = `
//                 <table class="table table-bordered">
//                     <thead>
//                         <tr>
//                             <th></th>
//                             <th>Delivery Note</th>
//                             <th>Item</th>
//                             <th>Qty</th>
//                             <th>Rate</th>
//                         </tr>
//                     </thead>
//                     <tbody>
//             `;

//             rows.forEach(r => {
//                 html += `
//                     <tr>
//                         <td>
//                             <input type="checkbox" class="dn-item-check"
//                                 data-delivery-note="${r.delivery_note}"
//                                 data-dn-item="${r.delivery_note_item}"
//                                 data-item-code="${r.item_code}"
//                                 data-item-name="${r.item_name}"
//                                 data-qty="${r.delivered_qty}"
//                                 data-rate="${r.rate}"
//                                 data-amount="${r.amount}">
//                         </td>
//                         <td>${r.delivery_note}</td>
//                         <td>${r.item_code} – ${r.item_name}</td>
//                         <td>${r.delivered_qty}</td>
//                         <td>${r.rate}</td>
//                     </tr>`;
//             });

//             html += "</tbody></table>";
//             dialog.fields_dict.items_html.set_value(html);
//         }
//     });
// }



function load_dn_items(dialog) {
    const customer = dialog.get_value("customer");
    const delivery_note = dialog.get_value("delivery_note");
    const item_code = dialog.get_value("item_code");
    const fetch_all = dialog.get_value("fetch_all");

    // ❌ customer mandatory
    if (!customer) {
        dialog.fields_dict.items_html.set_value("<p>Please select Customer</p>");
        return;
    }

    // ❌ nothing selected & fetch_all unchecked
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

// frappe.ui.form.on("Combined Delivery Note Return Item", {
//     store_qty(frm, cdt, cdn) {
//         update_remaining(cdt, cdn);
//     },
//     damage_qty(frm, cdt, cdn) {
//         update_remaining(cdt, cdn);
//     }
// });

// function update_remaining(cdt, cdn) {
//     let r = locals[cdt][cdn];
//     let returned = (r.store_qty || 0) + (r.damage_qty || 0);

//     // ❌ Over return block
//     if (returned > r.return_qty) {
//         frappe.msgprint("Return qty cannot exceed remaining qty");
//         r.store_qty = 0;
//         r.damage_qty = 0;
//         frappe.refresh_field("items");
//         return;
//     }

//     // ✅ Live remaining
//     r.delivered_qty = r.return_qty - returned;
//     frappe.refresh_field("items");
// }

// ===============================
// Auto Series for Return Document
// ===============================



