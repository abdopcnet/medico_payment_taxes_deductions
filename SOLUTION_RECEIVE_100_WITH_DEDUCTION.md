# الحل: استلام 100 مع خصم 1% بحيث تكون الفاتورة مدفوعة بالكامل

## تحليل الكود الفعلي

بناءً على تحليل الكود في ERPNext:

### 1. كيف يعمل Payment Entry

من الكود في `add_party_gl_entries()` (سطر 1305-1394):
```python
for d in self.get("references"):
    gle.update({
        dr_or_cr + "_in_account_currency": d.allocated_amount,  # يستخدم allocated_amount
        # ...
    })
    gle.update({
        "against_voucher_type": d.reference_doctype,  # Sales Invoice
        "against_voucher": d.reference_name,          # رقم الفاتورة
    })
```

**النتيجة:** `allocated_amount` فقط هو الذي يُستخدم لتسديد الفاتورة.

من الكود في `add_deductions_gl_entries()` (سطر 1653-1675):
```python
def add_deductions_gl_entries(self, gl_entries):
    for d in self.get("deductions"):
        gl_entries.append({
            "account": d.account,
            "against": self.party or self.paid_from,  # ضد العميل، وليس ضد الفاتورة
            "debit": d.amount,
        })
```

**النتيجة:** Deductions هي نفقات منفصلة، و**ليست** جزء من المبلغ المخصص للفاتورة.

### 2. مثال من Test Case

من `test_payment_entry_write_off_difference` (سطر 808-839):
```python
pe.received_amount = pe.paid_amount = 95  # استلم 95
pe.append("deductions", {"amount": 5})     # خصم 5
# allocated_amount = 100 (كامل مبلغ الفاتورة)

# GL Entries:
# ["Debtors - _TC", 0, 100, si.name]        # الفاتورة دُفعت 100 (allocated_amount)
# ["_Test Cash - _TC", 95, 0, None]         # استلم 95
# ["_Test Write Off - _TC", 5, 0, None]     # خصم 5 (ليس ضد الفاتورة)
```

## الحل الصحيح

### السيناريو: استلمت 100، الفاتورة = 100، تريد خصم 1% (1)

**❌ الطريقة الخاطئة:**
```
paid_amount = 100
allocated_amount = 99
deduction = 1
```
**النتيجة:** الفاتورة متبقية 1 (غير مدفوعة بالكامل)

**✅ الطريقة الصحيحة (من تحليل الكود):**

المعادلة من الكود:
```
paid_amount = allocated_amount + deduction
```

ولكي تكون الفاتورة مدفوعة بالكامل:
```
allocated_amount = invoice_grand_total
```

**الحل:**
```
Sales Invoice grand_total = 100
المبلغ المستلم = 99
الخصم (1%) = 1

Payment Entry:
- paid_amount = 99          (المبلغ المستلم فعلياً)
- allocated_amount = 100    (مبلغ الفاتورة الكامل)
- deduction amount = 1      (مبلغ الخصم)

GL Entries:
- Debtors: Credit 100 (ضد Sales Invoice) - الفاتورة مدفوعة بالكامل
- Cash: Debit 99 (المبلغ المستلم)
- حساب الخصم: Debit 1 (نفقة)
```

**لكن:** هذا يخلق `difference_amount = 0` لأنه:
- paid_amount (99) + deduction (1) = allocated_amount (100) ✓

### السيناريو: استلمت 100، الفاتورة = 101، تريد خصم 1% (1.01)

**الحل:**
```
Sales Invoice grand_total = 101
المبلغ المطلوب استلامه = 100
الخصم (1% من 101) = 1.01

❌ هذا لا يعمل! لأن:
paid_amount (100) + deduction (1.01) = 101.01 ≠ allocated_amount (101)

✅ الحل الصحيح:
يجب أن تستلم 101.01 لتغطي كامل الفاتورة (101) + الخصم (1.01)

Payment Entry:
- paid_amount = 101.01      (يجب استلام 101.01)
- allocated_amount = 101    (مبلغ الفاتورة الكامل)
- deduction amount = 1.01   (مبلغ الخصم)

GL Entries:
- Debtors: Credit 101 (ضد Sales Invoice) - الفاتورة مدفوعة بالكامل
- Cash: Debit 101.01 (المبلغ المستلم)
- حساب الخصم: Debit 1.01 (نفقة)

الرصيد: 101.01 - 101 - 1.01 = 0 ✓
```

## المبدأ الأساسي من تحليل الكود

**من الكود:**
1. `allocated_amount` يُستخدم مباشرة لدفع الفاتورة (سطر 1360, 1389-1390)
2. `deduction` تُنشئ قيد محاسبي منفصل، ليس ضد الفاتورة (سطر 1667)
3. **المعادلة المحاسبية:**
   ```
   paid_amount = allocated_amount + deduction
   ```

**لكي تكون الفاتورة مدفوعة بالكامل:**
```
allocated_amount = invoice_grand_total
```

**لذلك:**
```
paid_amount = invoice_grand_total + deduction
```

## الحل لمشكلتك

**الحالة:** الفاتورة = 114، استلمت 100، تريد خصم 14

**❌ لا يمكن!** لأن:
- `paid_amount` (100) + `deduction` (14) = 114 = `allocated_amount` (114) ✓
- لكنك استلمت 100 فقط، وليس 114!

**✅ الحل الصحيح:**

### خيار 1: استلم 114 (لدفع الفاتورة الكاملة + الخصم)
```
Payment Entry:
- paid_amount = 114        (يجب استلام 114)
- allocated_amount = 114   (مبلغ الفاتورة الكامل)
- deduction amount = 14    (مبلغ الخصم)

GL Entries:
- Debtors: Credit 114 (ضد Sales Invoice) - الفاتورة مدفوعة بالكامل
- Cash: Debit 114 (المبلغ المستلم)
- حساب الخصم: Debit 14 (نفقة)
```

### خيار 2: استلم 100 فقط (الفاتورة ستكون مدفوعة جزئياً)
```
Payment Entry:
- paid_amount = 100        (المبلغ المستلم)
- allocated_amount = 100   (جزء من الفاتورة)
- deduction amount = 0     (لا يوجد خصم)

GL Entries:
- Debtors: Credit 100 (ضد Sales Invoice) - الفاتورة متبقية 14
- Cash: Debit 100 (المبلغ المستلم)

النتيجة: الفاتورة "Partly Paid" مع باقي 14
```

## الخلاصة

**من تحليل الكود الفعلي:**

1. **`allocated_amount`** يُستخدم مباشرة لدفع الفاتورة
2. **`deduction`** هي نفقة منفصلة، وليست جزء من دفع الفاتورة
3. **المعادلة:** `paid_amount = allocated_amount + deduction`
4. **لكي تكون الفاتورة مدفوعة بالكامل:** `allocated_amount = invoice_grand_total`
5. **لذلك:** يجب أن تستلم `invoice_grand_total + deduction`

**لمشكلتك (الفاتورة = 114، تريد خصم 14):**
- يجب أن تستلم: **114 + 14 = 128**
- `paid_amount = 128`
- `allocated_amount = 114` (كامل الفاتورة)
- `deduction = 14`

**إذا استلمت 100 فقط:**
- `paid_amount = 100`
- `allocated_amount = 100` (الفاتورة ستكون مدفوعة جزئياً)
- `deduction = 0` (لا يوجد خصم)

**أو:**
- `paid_amount = 114` (لكنك تحتاج استلام 114، وليس 100)
- `allocated_amount = 114` (الفاتورة مدفوعة بالكامل)
- `deduction = 14`

## مثال عملي

**الحالة:** استلمت 100، الفاتورة = 100، تريد خصم 1% (1)

**✅ الحل الصحيح:**
```
Payment Entry:
- paid_amount = 99          (استلمت 99، الخصم 1)
- allocated_amount = 100    (كامل مبلغ الفاتورة)
- deduction = 1             (الخصم 1%)

النتيجة:
- الفاتورة مدفوعة بالكامل (allocated_amount = 100)
- المبلغ المستلم = 99
- الخصم = 1 (في حساب الخصم)
```

**المعادلة:** 99 + 1 = 100 ✓

