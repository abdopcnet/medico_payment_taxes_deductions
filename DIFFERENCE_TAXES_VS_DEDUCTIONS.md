# الفرق بين Taxes و Deductions في Payment Entry

## من تحليل الكود

### 1. Taxes Table (Payment Entry Tax)

**الاستخدام:**
- للضرائب والرسوم المرتبطة بالدفعة
- مثل: ضريبة القيمة المضافة، ضريبة الدخل، رسوم الخدمات

**من `add_tax_gl_entries()` (سطر 1588-1651):**
```python
def add_tax_gl_entries(self, gl_entries):
    for d in self.get("taxes"):
        # ...
        if not d.included_in_paid_amount:
            # ينشئ GL entry منفصل
            gl_entries.append({
                "account": payment_account,  # حساب البنك/الصندوق
                "against": party or paid_from,
                "debit/credit": tax_amount,
            })
```

**الخصائص:**
- يمكن أن تكون `included_in_paid_amount` = 1 (مشمولة في paid_amount)
- تؤثر على `paid_amount_after_tax` و `received_amount_after_tax`
- يمكن أن تكون Add أو Deduct
- تؤثر على `base_total_taxes_and_charges`

### 2. Deductions Table (Payment Entry Deduction)

**الاستخدام:**
- للخصومات والنفقات المنفصلة
- مثل: خصم تحت حساب الضريبة، رسوم الاستقطاع، خسائر الصرف

**من `add_deductions_gl_entries()` (سطر 1653-1675):**
```python
def add_deductions_gl_entries(self, gl_entries):
    for d in self.get("deductions"):
        # ...
        gl_entries.append({
            "account": d.account,  # حساب الخصم
            "against": self.party or self.paid_from,  # ضد العميل/المورد
            "debit": d.amount,  # دائماً debit
        })
```

**الخصائص:**
- دائماً `debit` (مدين)
- `against` = `party` (وليس ضد الفاتورة)
- تؤثر على `unallocated_amount` (من set_unallocated_amount)
- تؤثر على `difference_amount` (من set_difference_amount)
- لا تؤثر على `paid_amount_after_tax`

## الفروقات الأساسية

### 1. التأثير على الحسابات

**Taxes:**
- تؤثر على `paid_amount_after_tax`
- تؤثر على `received_amount_after_tax`
- يمكن أن تكون مشمولة في `paid_amount` (`included_in_paid_amount`)

**Deductions:**
- لا تؤثر على `paid_amount_after_tax`
- تؤثر على `unallocated_amount`
- تؤثر على `difference_amount`
- دائماً منفصلة عن `paid_amount`

### 2. GL Entries

**Taxes:**
- يمكن أن تكون `debit` أو `credit` (حسب Add/Deduct)
- `against` = `party` أو `paid_from`/`paid_to`
- قد تكون مشمولة في حساب البنك

**Deductions:**
- دائماً `debit` (مدين)
- `against` = `party` أو `paid_from`
- دائماً في حساب منفصل (حساب الخصم)

### 3. التأثير على الفاتورة

**Taxes:**
- لا تؤثر مباشرة على `allocated_amount`
- لا تؤثر على `outstanding_amount` في الفاتورة

**Deductions:**
- لا تؤثر مباشرة على `allocated_amount`
- لا تؤثر على `outstanding_amount` في الفاتورة
- لكنها تؤثر على `unallocated_amount` و `difference_amount`

## مثال عملي

### الحالة: الفاتورة = 114، استلمت = 114، خصم = 4

**إذا وضعت 4 في Taxes:**
```
paid_amount = 114
taxes[0].amount = 4
paid_amount_after_tax = 118 (إذا كانت Add)
أو paid_amount_after_tax = 110 (إذا كانت Deduct)

GL Entries:
- Debtors: Credit 114 (ضد الفاتورة)
- Cash: Debit 114
- Tax Account: Credit/Debit 4 (حسب Add/Deduct)
```

**إذا وضعت 4 في Deductions:**
```
paid_amount = 114
deductions[0].amount = 4
unallocated_amount = 4 (يحسبه النظام)
difference_amount = 0 (يحسبه النظام)

GL Entries:
- Debtors: Credit 114 (ضد الفاتورة)
- Debtors: Credit 4 (unallocated, ضد Payment Entry)
- Cash: Debit 114
- Deduction Account: Debit 4 (ضد party)
```

## الخلاصة

### استخدم Taxes عندما:
- المبلغ هو ضريبة أو رسوم مرتبطة بالدفعة
- تريد أن يؤثر على `paid_amount_after_tax`
- يمكن أن تكون مشمولة في `paid_amount`

### استخدم Deductions عندما:
- المبلغ هو خصم أو نفقة منفصلة
- تريد أن يؤثر على `unallocated_amount`
- المبلغ ليس ضريبة (مثل: خصم تحت حساب الضريبة، رسوم استقطاع)

## في حالتك (خصم 4)

**الصحيح: Deductions**
- لأن المبلغ هو "خصم تحت حساب الضريبة"
- ليس ضريبة، بل خصم
- يجب أن يؤثر على `unallocated_amount` و `difference_amount`

**❌ خطأ: Taxes**
- لأن المبلغ ليس ضريبة
- سيؤثر على `paid_amount_after_tax` (غير مرغوب)
- لن يؤثر على `unallocated_amount` بشكل صحيح

