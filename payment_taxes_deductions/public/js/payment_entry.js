// ============================================================================
// PAYMENT ENTRY CLIENT SCRIPT
// ============================================================================
// Handles automatic deduction calculation when custom_deduction field changes
// and updates deduction amounts based on Sales Taxes and Charges Template
// and Tax Set-Up documents

// ============================================================================
// SECTION 1: HELPER FUNCTIONS
// ============================================================================
// Utility functions for fetching data and calculating deductions

/**
 * Fetch taxes from Sales Taxes and Charges Template
 * @param {string} template - Name of the Sales Taxes and Charges Template
 * @returns {Promise<Array>} Array of tax objects from the template
 */
async function fetchTemplateTaxes(template) {
	console.log("Fetching template taxes for:", template);
	return new Promise((resolve, reject) => {
		frappe.call({
			method: "frappe.client.get",
			args: {
				doctype: "Sales Taxes and Charges Template",
				name: template,
			},
			callback: function (r) {
				if (r.message) {
					console.log("Fetched template taxes:", r.message.taxes);
					resolve(r.message.taxes);
				} else {
					console.warn("No taxes found for template:", template);
					reject("No taxes found for template: " + template);
				}
			},
		});
	});
}

/**
 * Process a single reference (Sales Invoice) to calculate base total
 * @param {Object} reference - Payment Entry Reference object
 * @returns {Promise<number>} Calculated result (grand_total - base_total_taxes_and_charges)
 */
function process_reference(reference) {
	console.log("Processing reference:", reference.reference_name);
	return new Promise((resolve, reject) => {
		frappe.call({
			method: "frappe.client.get",
			args: {
				doctype: "Sales Invoice",
				name: reference.reference_name,
			},
			callback: function (r) {
				if (r.message) {
					let grand_total = r.message.grand_total;
					let base_total_taxes_and_charges = r.message.base_total_taxes_and_charges;
					let result = grand_total - base_total_taxes_and_charges;
					console.log(
						`Invoice ${reference.reference_name}: grand_total = ${grand_total}, base_total_taxes_and_charges = ${base_total_taxes_and_charges}, result = ${result}`
					);
					resolve(result);
				} else {
					console.warn("No invoice found for reference:", reference.reference_name);
					resolve(0); // Default to 0 if no invoice found
				}
			},
			error: function (err) {
				console.error("Error fetching invoice:", err);
				reject("Error fetching invoice: " + err);
			},
		});
	});
}

/**
 * Process all references and calculate total base total
 * @param {Array} references - Array of Payment Entry Reference objects
 * @returns {Promise<number>} Sum of (grand_total - base_total_taxes_and_charges) for all references
 */
async function processReferences(references) {
	let total_base_total = 0;
	console.log("Processing references...");

	for (let reference of references) {
		try {
			let result = await process_reference(reference);
			console.log(`Processed reference ${reference.reference_name}: result =`, result);
			total_base_total += result; // sum of (base_total - base_total_taxes_and_charges)
		} catch (error) {
			console.error("Error processing reference:", error);
		}
	}

	console.log("Total base total after processing references:", total_base_total);
	return total_base_total;
}

/**
 * Fetch Tax Set-Up document data
 * @param {string} template - Name of the Tax Set-Up document (uses template name)
 * @returns {Promise<Object>} Tax Set-Up document data
 */
async function fetchTaxSetup(template) {
	console.log("Fetching Tax Set-Up for template:", template);
	return new Promise((resolve, reject) => {
		frappe.call({
			method: "frappe.client.get",
			args: {
				doctype: "Tax Set-Up",
				name: template,
			},
			callback: function (r) {
				if (r.message) {
					console.log("Fetched Tax Set-Up:", r.message);
					resolve(r.message);
				} else {
					console.warn("No Tax Set-Up found for template:", template);
					reject("No Tax Set-Up found for template: " + template);
				}
			},
			error: function (err) {
				console.error("Error fetching Tax Set-Up:", err);
				reject("Error fetching Tax Set-Up: " + err);
			},
		});
	});
}

/**
 * Calculate deduction amounts based on Tax Set-Up and total base total
 * Updates deduction amounts in the form's deductions table
 * @param {Object} taxSetup - Tax Set-Up document data
 * @param {number} total_base_total - Total base total from all references
 * @param {Object} frm - Frappe form object
 */
function calculateDeductions(taxSetup, total_base_total, frm) {
	console.log("Calculating deductions...");
	let adjusted_total = total_base_total;
	let percentage_to_use = 0;

	// Determine the percentage based on the total_base_total range
	taxSetup.table_yljg.forEach((child) => {
		if (total_base_total >= child.from && total_base_total < child.to) {
			percentage_to_use = child.percentage;
			console.log(
				`Percentage for original total_base_total ${total_base_total} found: ${percentage_to_use}`
			);
		}
	});

	let final_amount = 0;

	// Calculate final amount based on total_base_total range
	if (total_base_total >= 10001) {
		// Adjusted calculation for totals >= 10,001
		adjusted_total -= 10050; // Subtract 10,050
		final_amount = adjusted_total * percentage_to_use + 640; // Apply (percentage + 640)
		console.log(
			`New final amount for adjusted total ${adjusted_total} with (percentage + 640):`,
			final_amount
		);
	} else {
		// Calculation for totals < 10,000
		adjusted_total -= 50; // Subtract 50
		final_amount = adjusted_total * (percentage_to_use / 100); // Apply percentage as a percentage
		console.log(
			`Final amount for adjusted total ${adjusted_total} with ${percentage_to_use}%:`,
			final_amount
		);
	}

	// Split final amount: 1/4 for regular stamp, 3/4 for additional stamp
	let quarter_result = final_amount / 4;
	let remaining_three_quarters = quarter_result * 3;
	console.log(
		`Quarter result: ${quarter_result}, Remaining three quarters: ${remaining_three_quarters}`
	);

	// Account names for deduction assignment
	let first_quarter_account = "5232 - دمغة عادية - M";
	let remaining_quarters_account = "5233 - دمغة اضافية - M";
	let calculated_account = "2302 - ارباح تجارية وصناعية - M";
	let vat_account = "5204 - Entertainment Expenses - F";

	// Update deduction amounts based on account
	frm.doc.deductions.forEach((deduction) => {
		if (deduction.account === first_quarter_account) {
			deduction.amount = quarter_result;
			console.log(`Assigned ${quarter_result} to account ${first_quarter_account}`);
		} else if (deduction.account === remaining_quarters_account) {
			deduction.amount = remaining_three_quarters;
			console.log(
				`Assigned ${remaining_three_quarters} to account ${remaining_quarters_account}`
			);
		} else if (deduction.account === calculated_account || deduction.account === vat_account) {
			let calculated_amount = total_base_total * (1 / 100);
			deduction.amount = calculated_amount;
			console.log(
				`Assigned calculated amount ${calculated_amount} to account ${deduction.account}`
			);
		}
	});
}

/**
 * Update custom_total_taxes field with sum of all deduction amounts
 * @param {Object} frm - Frappe form object
 */
function updateTotalTaxes(frm) {
	let total_taxes = frm.doc.deductions.reduce(
		(sum, deduction) => sum + (deduction.amount || 0),
		0
	);
	console.log("Updating total taxes:", total_taxes);
	frm.set_value("custom_total_taxes", total_taxes);
	frm.refresh_field("custom_total_taxes");
}

/**
 * Calculate total tax amount and net total for taxes table
 * Used by the "حساب الضرائب والدمغات" button
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

	console.log("Total tax amount:", totalTaxAmount);
	console.log("Net total:", net);

	// Refresh and save
	frm.refresh_field("taxes");
	frm.save();
}

// ============================================================================
// SECTION 2: PAYMENT ENTRY FORM HANDLERS
// ============================================================================
// Handlers for Payment Entry form events: refresh button and custom_deduction field

frappe.ui.form.on("Payment Entry", {
	/**
	 * Add custom button to calculate taxes and stamps
	 * Button "حساب الضرائب والدمغات" calculates taxes based on server method 'test'
	 * and populates the taxes table with 9 tax rows
	 */
	refresh: function (frm) {
		// Add custom button labeled 'حساب الضرائب والدمغات'
		frm.add_custom_button(__("حساب الضرائب والدمغات"), function () {
			// Get the paid amount from the form
			let paid_amount = flt(frm.doc.paid_amount);
			let table = frm.doc.taxes;

			// Clear existing taxes table
			if (Array.isArray(table) && table.length > 0) {
				while (table.length > 0) {
					table.pop();
				}
			}

			// Get tax accounts from Payment Deductions Accounts based on company
			let company = frm.doc.company;
			frappe.call({
				method: "payment_taxes_deductions.payment_taxes_deductions.doctype.payment_deductions_accounts.payment_deductions_accounts.get_tax_accounts",
				args: {
					company: company,
				},
				callback: function (accounts_r) {
					if (accounts_r.exc) {
						frappe.msgprint(__("Error loading tax accounts"));
						return;
					}

					let tax_accounts = accounts_r.message;

					// Make server call to method 'test'
					frappe.call({
						method: "payment_taxes_deductions.payment_taxes_deductions.payment_entry.test",
						args: {
							total: paid_amount,
						},
						callback: function (r) {
							if (!r.exc) {
								// Get tax amounts from server response
								let atvat = r.message[0]["الارباح التجارية"];
								let atvat2 = r.message[0]["الدمغة العادية"];
								let atvat3 = r.message[0]["الدمغة التدريجية"];
								let contract = frm.doc.contract_papers_qty * 3 * 0.9;

								// Add tax rows to taxes table using accounts from settings
								frm.add_child("taxes", {
									add_deduct_tax: "Deduct",
									charge_type: "Actual",
									account_head: tax_accounts.commercial_profits,
									tax_amount: atvat,
									description: "ارباح تجارية",
								});

								frm.add_child("taxes", {
									add_deduct_tax: "Deduct",
									charge_type: "Actual",
									account_head: tax_accounts.regular_stamp,
									tax_amount: atvat2,
									description: "دمغة عادية",
								});

								frm.add_child("taxes", {
									add_deduct_tax: "Deduct",
									charge_type: "Actual",
									account_head: tax_accounts.additional_stamp,
									tax_amount: atvat3,
									description: "دمغة اضافية",
								});

								frm.add_child("taxes", {
									add_deduct_tax: "Deduct",
									charge_type: "Actual",
									account_head: tax_accounts.qaderon_difference,
									tax_amount: 0,
									description: "قادرون باختلاف",
								});

								frm.add_child("taxes", {
									add_deduct_tax: "Deduct",
									charge_type: "Actual",
									account_head: tax_accounts.contract_stamp,
									tax_amount: contract,
									description: "دمغة عقد",
								});

								frm.add_child("taxes", {
									add_deduct_tax: "Deduct",
									charge_type: "Actual",
									account_head: tax_accounts.check_stamp,
									tax_amount: 0,
									description: "دمغة شيك",
								});

								frm.add_child("taxes", {
									add_deduct_tax: "Deduct",
									charge_type: "Actual",
									account_head: tax_accounts.applied_professions_tax,
									tax_amount: 0,
									description: "ضريبة المهن التطبيقية",
								});

								frm.add_child("taxes", {
									add_deduct_tax: "Deduct",
									charge_type: "Actual",
									account_head: tax_accounts.medical_professions_tax,
									tax_amount: 0,
									description: "ضريبة المهن الطبية",
								});

								// Add VAT 20% if Sales Invoice has taxes_and_charges
								if (
									frm.doc.references &&
									frm.doc.references[0] &&
									frm.doc.references[0].reference_name
								) {
									let ref = frm.doc.references[0].reference_name;
									frappe.db.get_doc("Sales Invoice", ref).then((vat_inv) => {
										if (vat_inv.taxes_and_charges) {
											frm.add_child("taxes", {
												add_deduct_tax: "Deduct",
												charge_type: "Actual",
												account_head: tax_accounts.vat_20_percent,
												tax_amount: frm.doc.paid_amount * 0.14 * 0.2,
												description: "20% من القيمة المضافة",
											});
										}

										// Calculate total tax amount and net total
										calculateTaxTotalAndNet(frm, paid_amount);
									});
								} else {
									// Calculate total tax amount and net total without VAT
									calculateTaxTotalAndNet(frm, paid_amount);
								}
							}
						},
					});
				},
			});
		});
	},

	/**
	 * Handle custom_deduction field change
	 * Automatically calculates and populates deductions table when template is selected
	 */
	custom_deduction: async function (frm) {
		console.log("Starting custom deduction process...");

		// Clear existing deductions
		frm.clear_table("deductions");
		console.log("Cleared existing deductions.");

		// Get the selected Sales Taxes and Charges Template
		let template = frm.doc.custom_deduction;
		if (!template) {
			console.log("No template selected.");
			return;
		}
		console.log("Selected template:", template);

		try {
			// Fetch the Sales Taxes and Charges Template data
			let taxes = await fetchTemplateTaxes(template);
			console.log("Taxes fetched:", taxes);

			// Add deduction rows from template
			taxes.forEach((tax) => {
				let deduction = frm.add_child("deductions");
				deduction.account = tax.account_head;
				deduction.amount = tax.tax_amount;
				console.log("Added deduction:", deduction);
			});

			frm.refresh_field("deductions");
			console.log("Deductions table refreshed.");

			// Process references to calculate total base total
			let total_base_total = await processReferences(frm.doc.references);
			console.log("Total result from all references:", total_base_total);

			// Fetch the Tax Set-Up data
			let taxSetup = await fetchTaxSetup(template);
			console.log("Tax Set-Up fetched:", taxSetup);

			// Calculate deductions based on Tax Set-Up
			calculateDeductions(taxSetup, total_base_total, frm);

			frm.refresh_field("deductions");
			console.log("Final deductions table refreshed.");

			// Update custom_total_taxes field with sum of all deductions
			updateTotalTaxes(frm);
			console.log("Total taxes updated.");
		} catch (error) {
			console.error("Error in processing deductions:", error);
		}
	},
});

// ============================================================================
// SECTION 3: PAYMENT ENTRY DEDUCTION TABLE HANDLERS
// ============================================================================

frappe.ui.form.on("Payment Entry Deduction", {
	/**
	 * Handle deduction row addition
	 * Updates total taxes when a new deduction row is added
	 */
	deductions_add: function (frm, cdt, cdn) {
		console.log("Deduction added. Updating total taxes...");
		updateTotalTaxes(frm);
	},

	/**
	 * Handle deduction row removal
	 * Updates total taxes when a deduction row is removed
	 */
	deductions_remove: function (frm, cdt, cdn) {
		console.log("Deduction removed. Updating total taxes...");
		updateTotalTaxes(frm);
	},

	/**
	 * Handle deduction amount change
	 * Updates total taxes when deduction amount is modified
	 */
	amount: function (frm, cdt, cdn) {
		console.log("Deduction amount changed. Updating total taxes...");
		updateTotalTaxes(frm);
	},
});
