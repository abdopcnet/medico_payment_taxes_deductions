// ============================================================================
// PAYMENT ENTRY CLIENT SCRIPT
// ============================================================================
// Handles tax calculation button "Calculate Taxes and Stamps"
// Uses Payment Deductions Accounts for account names
// Uses Stamp Tax Calculation Rules for percentages/ranges

// ============================================================================
// SECTION 1: HELPER FUNCTIONS
// ============================================================================
// Utility functions for tax calculations

/**
 * Calculate total tax amount and net total for taxes table
 * Used by the "Calculate Taxes and Stamps" button
 * @param {Object} frm - Frappe form object
 * @param {number} paid_amount - Paid amount from Payment Entry
 */
function calculateTaxTotalAndNet(frm, paid_amount) {
	let totalTaxAmount = 0;
	let taxes = frm.doc.taxes;

	// Sum all tax amounts
	for (let i = 0; i < taxes.length; i++) {
		let tax = taxes[i];
		totalTaxAmount += tax.tax_amount || 0;
	}

	// Calculate net total
	let net = paid_amount - totalTaxAmount;
	frm.doc.custom_net_total = net;

	console.log('Total tax amount:', totalTaxAmount);
	console.log('Net total:', net);

	// Refresh and save
	frm.refresh_field('taxes');
	frm.save();
}

// ============================================================================
// SECTION 2: PAYMENT ENTRY FORM HANDLERS
// ============================================================================
// Handlers for Payment Entry form events: refresh button

frappe.ui.form.on('Payment Entry', {
	/**
	 * Auto-fetch customer group when party (Customer) is selected
	 * Only for payment_type = "Receive" and party_type = "Customer"
	 */
	party: function (frm) {
		if (
			frm.doc.payment_type === 'Receive' &&
			frm.doc.party_type === 'Customer' &&
			frm.doc.party
		) {
			frappe.db.get_value('Customer', frm.doc.party, 'customer_group', (r) => {
				if (r && r.customer_group) {
					frm.set_value('custom_customer_group', r.customer_group);
				}
			});
		} else {
			// Clear customer group if not Customer Receive
			if (frm.doc.custom_customer_group) {
				frm.set_value('custom_customer_group', '');
			}
		}
	},

	/**
	 * Add custom buttons for tax calculations and deductions
	 * Only works for draft documents (docstatus == 0) and Receive payment type
	 */
	refresh: function (frm) {
		// Only show button for draft documents and Receive payment type
		if (frm.doc.docstatus === 0 && frm.doc.payment_type === 'Receive') {
			// Add direct orange button to fetch deductions based on customer group
			frm.page.add_inner_button(
				__('Download Deductions'),
				function () {
					// Validate required fields
					if (!frm.doc.company) {
						frappe.msgprint(__('Company is required'));
						return;
					}

					if (!frm.doc.custom_customer_group) {
						frappe.msgprint(
							__('Customer Group is required. Please select a Customer first.'),
						);
						return;
					}

					if (!frm.doc.paid_amount || flt(frm.doc.paid_amount) <= 0) {
						frappe.msgprint(__('Paid Amount is required and must be greater than 0'));
						return;
					}

					// Get deductions from server
					frappe.call({
						method: 'payment_taxes_deductions.payment_taxes_deductions.payment_entry.get_deductions_by_customer_group',
						args: {
							company: frm.doc.company,
							customer_group: frm.doc.custom_customer_group,
							paid_amount: frm.doc.paid_amount,
						},
						callback: function (r) {
							if (r.exc) {
								frappe.msgprint(__('Error loading deductions: {0}', [r.exc]));
								return;
							}

							if (!r.message || r.message.length === 0) {
								frappe.msgprint(
									__('No deductions found for this company and customer group'),
								);
								return;
							}

							// Clear existing deductions table
							if (frm.doc.deductions && frm.doc.deductions.length > 0) {
								frm.clear_table('deductions');
							}

							// Add deduction rows
							r.message.forEach(function (deduction) {
								frm.add_child('deductions', {
									account: deduction.account,
									cost_center: deduction.cost_center,
									amount: deduction.amount,
									description: deduction.description,
								});
							});

							// Refresh deductions table
							frm.refresh_field('deductions');
							frappe.show_alert({
								message: __('Deductions loaded successfully'),
								indicator: 'green',
							});
						},
					});
				},
				null,
				'warning',
			);
		}
	},
});
