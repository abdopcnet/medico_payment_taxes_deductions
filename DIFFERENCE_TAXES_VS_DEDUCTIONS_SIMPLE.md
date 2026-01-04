# الفرق بين Taxes و Deductions - شرح بسيط

## Taxes (الضرائب)

**الاستخدام:**
- للضرائب والرسوم (مثل: ضريبة القيمة المضافة، ضريبة الدخل)

**الحقول:**
- `account_head` = حساب الضريبة
- `tax_amount` = مبلغ الضريبة
- `add_deduct_tax` = "Add" أو "Deduct"
- `included_in_paid_amount` = 0 أو 1

**التأثير:**
- يؤثر على `paid_amount_after_tax`
- يؤثر على `received_amount_after_tax`
- يؤثر على `base_total_taxes_and_charges`
- يمكن أن تكون debit أو credit (حسب Add/Deduct)

**GL Entries:**
- ينشئ قيدين (إذا كانت غير مشمولة في paid_amount):
  1. حساب الضريبة: debit/credit حسب Add/Deduct
  2. حساب البنك: credit/debit (مقابل)

## Deductions (الخصومات)

**الاستخدام:**
- للخصومات والنفقات المنفصلة (مثل: خصم تحت حساب الضريبة، رسوم الاستقطاع)

**الحقول:**
- `account` = حساب الخصم
- `amount` = مبلغ الخصم
- `cost_center` = مركز التكلفة

**التأثير:**
- يؤثر على `unallocated_amount`
- يؤثر على `difference_amount`
- **لا يؤثر** على `paid_amount_after_tax`

**GL Entries:**
- ينشئ قيد واحد:
  - حساب الخصم: debit دائماً
  - `against` = party (العميل/المورد)

## الفروقات الأساسية

| الميزة | Taxes | Deductions |
|--------|-------|------------|
| **التأثير على paid_amount_after_tax** | ✅ نعم | ❌ لا |
| **التأثير على unallocated_amount** | ❌ لا | ✅ نعم |
| **التأثير على difference_amount** | ❌ لا | ✅ نعم |
| **Debit أو Credit** | حسب Add/Deduct | دائماً Debit |
| **عدد GL Entries** | 2 (إذا غير مشمولة) | 1 |
| **ضد ماذا (Against)** | party أو paid_from/paid_to | party |

## مثال عملي

### الحالة: خصم 4

**✅ الصحيح: Deductions**
```
deductions[0].account = حساب الخصم
deductions[0].amount = 4

النتيجة:
- unallocated_amount = 4 (يحسبه النظام)
- difference_amount = 0 (يحسبه النظام)
- GL Entry: حساب الخصم Debit 4 (ضد party)
```

**❌ خطأ: Taxes**
```
taxes[0].account_head = حساب الخصم
taxes[0].tax_amount = 4

النتيجة:
- paid_amount_after_tax = 118 (إذا Add) أو 110 (إذا Deduct)
- لا يؤثر على unallocated_amount
- GL Entries: 2 قيود (حساب الضريبة + حساب البنك)
```

## الخلاصة

**استخدم Taxes عندما:**
- المبلغ هو ضريبة أو رسوم
- تريد أن يؤثر على `paid_amount_after_tax`

**استخدم Deductions عندما:**
- المبلغ هو خصم أو نفقة منفصلة
- تريد أن يؤثر على `unallocated_amount` و `difference_amount`
- المبلغ ليس ضريبة

## في حالتك (خصم 4)

**الصحيح: Deductions** ✅
- لأن المبلغ هو "خصم تحت حساب الضريبة"
- يجب أن يؤثر على `unallocated_amount`

