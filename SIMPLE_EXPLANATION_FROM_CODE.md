# شرح مبسط من تحليل الكود

## Payment Entry - كيف يعمل

### الحقول الأساسية

**1. paid_amount:**
- المبلغ المدفوع/المستلم
- يدخله المستخدم

**2. received_amount:**
- المبلغ المستلم
- إذا كانت العملات متطابقة، = paid_amount تلقائياً

**3. total_allocated_amount:**
- مجموع allocated_amount من جدول references
- يحسبه النظام تلقائياً

**4. unallocated_amount:**
- المبلغ غير المخصص
- يحسبه النظام: `(paid_amount + deductions - total_allocated_amount)`

**5. difference_amount:**
- الفرق المحاسبي
- يجب أن يكون = 0 للسماح بالـ Submit
- يحسبه النظام: `(total_allocated_amount + unallocated_amount - received_amount - deductions)`

### جدول References (Payment Entry Reference)

**الحقول:**
- `reference_doctype` = نوع المستند (Sales Invoice, Purchase Invoice, etc.)
- `reference_name` = رقم المستند
- `allocated_amount` = المبلغ المخصص للمستند

**الاستخدام:**
- يحدد أي فواتير/مستندات سيتم الدفع لها
- `allocated_amount` = المبلغ الذي سيُدفع للمستند

**من الكود:**
- `allocated_amount` يُستخدم مباشرة لإنشاء GL entry ضد المستند
- `against_voucher_type` = reference_doctype
- `against_voucher_no` = reference_name

### جدول Deductions (Payment Entry Deduction)

**الحقول:**
- `account` = حساب الخصم
- `amount` = مبلغ الخصم
- `cost_center` = مركز التكلفة

**الاستخدام:**
- للخصومات والنفقات المنفصلة

**من الكود:**
- دائماً debit (مدين)
- `against` = party (العميل/المورد، وليس الفاتورة)
- يؤثر على `unallocated_amount`
- يؤثر على `difference_amount`

### جدول Taxes (Payment Entry Tax)

**الحقول:**
- `account_head` = حساب الضريبة
- `tax_amount` = مبلغ الضريبة
- `add_deduct_tax` = "Add" أو "Deduct"
- `included_in_paid_amount` = 0 أو 1

**الاستخدام:**
- للضرائب والرسوم

**من الكود:**
- يؤثر على `paid_amount_after_tax`
- يمكن أن تكون debit أو credit (حسب Add/Deduct)
- قد تكون مشمولة في `paid_amount`

## المعادلات الأساسية (من الكود)

### 1. total_allocated_amount:
```
total_allocated_amount = مجموع references[].allocated_amount
```

### 2. unallocated_amount (لـ Receive):
```
unallocated_amount = (paid_amount + deductions - total_allocated_amount) / source_exchange_rate
```

### 3. difference_amount (لـ Receive):
```
base_unallocated_amount = unallocated_amount * source_exchange_rate
base_party_amount = total_allocated_amount + base_unallocated_amount
difference_amount = base_party_amount - received_amount - deductions
```

### 4. للفاتورة مسددة بالكامل:
```
allocated_amount = invoice_grand_total
```

## GL Entries (من الكود)

### 1. Party GL Entry (من add_party_gl_entries):
```
لـ references:
- account = party_account (Debtors/Creditors)
- credit/debit = allocated_amount
- against_voucher_type = reference_doctype
- against_voucher_no = reference_name
```

### 2. Deductions GL Entry (من add_deductions_gl_entries):
```
لـ deductions:
- account = deduction_account
- debit = amount
- against = party (وليس الفاتورة)
```

### 3. Bank GL Entry (من add_bank_gl_entries):
```
- account = paid_to (لـ Receive)
- debit = received_amount
```

### 4. Unallocated GL Entry (من add_party_gl_entries):
```
إذا unallocated_amount > 0:
- account = party_account
- credit/debit = unallocated_amount
- against_voucher_type = "Payment Entry"
- against_voucher_no = payment_entry_name
```

## Payment Reconciliation (من الكود)

**الاستخدام:**
- لمطابقة المدفوعات مع الفواتير
- لحساب المبالغ المستحقة

**من payment_reconciliation:**
- يجلب الفواتير غير المسددة
- يجلب المدفوعات غير المطابقة
- يسمح بالمطابقة بينهما

**من payment_reconciliation_allocation:**
- يحدد المبالغ المطابقة بين الدفعة والفاتورة

**من payment_reconciliation_invoice:**
- تفاصيل الفاتورة في المطابقة

**من payment_reconciliation_payment:**
- تفاصيل الدفعة في المطابقة

## مثال عملي (من الكود)

### السيناريو: الفاتورة = 114، استلمت = 114، خصم = 4

**الحقول:**
```
paid_amount = 114
received_amount = 114
references[0].allocated_amount = 114
deductions[0].amount = 4
```

**الحقول المحسوبة تلقائياً:**
```
total_allocated_amount = 114
unallocated_amount = (114 + 4 - 114) / 1 = 4
difference_amount = (114 + 4) - 114 - 4 = 0
```

**GL Entries:**
```
1. Debtors: Credit 114 (ضد Sales Invoice ACC-SINV-2026-00001)
2. Debtors: Credit 4 (ضد Payment Entry ACC-PAY-2026-00001 - unallocated)
3. Cash: Debit 114
4. Deduction Account: Debit 4 (ضد party)
```

**النتيجة:**
- الفاتورة مسددة بالكامل (allocated_amount = 114)
- difference_amount = 0 (يمكن Submit)
- unallocated_amount = 4

## الخلاصة

**الحقول الأساسية:**
1. `paid_amount` = المبلغ المدفوع
2. `received_amount` = المبلغ المستلم
3. `references[].allocated_amount` = المبلغ المخصص للفاتورة
4. `deductions[].amount` = مبلغ الخصم

**الحقول المحسوبة:**
1. `total_allocated_amount` = مجموع allocated_amount
2. `unallocated_amount` = paid_amount + deductions - total_allocated_amount
3. `difference_amount` = يجب أن يكون 0

**للفاتورة مسددة بالكامل:**
- `allocated_amount` = `invoice_grand_total`

