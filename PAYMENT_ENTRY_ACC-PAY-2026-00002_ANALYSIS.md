# تحليل Payment Entry ACC-PAY-2026-00002

## البيانات الفعلية

### Payment Entry
```
- name: ACC-PAY-2026-00002
- payment_type: Receive
- paid_amount: 114.00
- received_amount: 114.00
- total_allocated_amount: 110.00  ⚠️ المشكلة هنا!
- unallocated_amount: 8.00
- difference_amount: 0.00
- docstatus: 1 (Submitted)
```

### Payment Entry Reference
```
- reference_doctype: Sales Invoice
- reference_name: ACC-SINV-2026-00001
- allocated_amount: 110.00  ⚠️ المشكلة هنا!
- outstanding_amount: 4.00
```

### Payment Entry Deduction
```
- account: 115201 - الخصم تحت حساب الضريبة...
- amount: 4.00
```

### Sales Invoice
```
- name: ACC-SINV-2026-00001
- grand_total: 114.00
- outstanding_amount: 4.00  ⚠️ الفاتورة متبقية 4
- status: Partly Paid
```

### Payment Ledger Entry

**Entry ضد الفاتورة:**
```
- voucher_type: Payment Entry
- voucher_no: ACC-PAY-2026-00002
- against_voucher_type: Sales Invoice
- against_voucher_no: ACC-SINV-2026-00001
- amount: -110.00  ⚠️ فقط 110 دُفع للفاتورة
```

**Entry للـ unallocated:**
```
- voucher_type: Payment Entry
- voucher_no: ACC-PAY-2026-00002
- against_voucher_type: Payment Entry
- against_voucher_no: ACC-PAY-2026-00002
- amount: -8.00
```

**مجموع Payment Ledger Entry ضد الفاتورة:**
```
- Sales Invoice original: +114.00
- Payment Entry payment: -110.00
- Outstanding = 114 - 110 = 4.00 ✓
```

## تحليل المشكلة

### المشكلة الرئيسية

**allocated_amount = 110** وليس 114!

### كيف يعمل النظام (من الكود)

من الكود في `add_party_gl_entries()` (سطر 1360, 1389-1390):
- يستخدم `d.allocated_amount` مباشرة لإنشاء GL entry ضد الفاتورة
- يضع `against_voucher_type` = "Sales Invoice"
- يضع `against_voucher_no` = رقم الفاتورة

**النتيجة:**
- المبلغ المدفوع للفاتورة = allocated_amount = 110
- مبلغ الفاتورة = 114
- المتبقي = 114 - 110 = 4
- الفاتورة = "Partly Paid"

### لماذا allocated_amount = 110؟

المستخدم وضع allocated_amount = 110 خطأً في جدول References.

### تأثير cheque_module

من فحص الكود:
- `cheque_module` يضيف custom fields فقط (custom_cheques_table, etc.)
- لا يعدل `allocated_amount` أو `total_allocated_amount`
- JavaScript في cheque_module يتعامل فقط مع Cheques Table
- لا يوجد hooks في cheque_module تعدل Payment Entry logic

**النتيجة:** cheque_module لا يؤثر على المشكلة.

### تأثير payment_taxes_deductions

من فحص الكود:
- `payment_taxes_deductions` يضيف `before_validate` hook
- يحسب taxes فقط
- لا يعدل `allocated_amount`

**النتيجة:** payment_taxes_deductions لا يؤثر على المشكلة.

## الحل

### البيانات الصحيحة

**allocated_amount يجب أن يكون = 114** (مبلغ الفاتورة الكامل)

### الخيار 1: دفع الفاتورة بالكامل مع خصم

```
Paid Amount = 118          (114 للفاتورة + 4 للخصم)
Allocated Amount = 114     (مبلغ الفاتورة الكامل)
Deduction Amount = 4
```

**المعادلة:**
```
paid_amount = allocated_amount + deduction
118 = 114 + 4 ✓
```

### الخيار 2: دفع الفاتورة بالكامل بدون خصم

```
Paid Amount = 114
Allocated Amount = 114     (مبلغ الفاتورة الكامل)
Deduction Amount = 0
```

### الخيار 3: دفع جزئي مع خصم (الوضع الحالي)

```
Paid Amount = 114
Allocated Amount = 110     (جزء من الفاتورة)
Deduction Amount = 4
```

**النتيجة:** الفاتورة متبقية 4 (Partly Paid)

## الخلاصة

1. **المشكلة:** allocated_amount = 110 (يجب أن يكون 114)
2. **السبب:** البيانات المدخلة خاطئة
3. **cheque_module:** لا يؤثر (يضيف custom fields فقط)
4. **payment_taxes_deductions:** لا يؤثر (يحسب taxes فقط)
5. **الحل:** ضبط allocated_amount = 114

**لدفع الفاتورة بالكامل:**
- allocated_amount = 114 (مبلغ الفاتورة الكامل)
- paid_amount = 118 (114 + 4 للخصم)
- deduction = 4
