# الخطوات الصحيحة - أسماء الحقول فقط

## السيناريو
- الفاتورة = 114
- استلمت = 110
- تريد خصم = 4
- تريد: الفاتورة مسددة بالكامل

## الخطوات

### 1. في Payment Entry - الحقول الأساسية:

```
paid_amount = 114
received_amount = 114
```

### 2. في جدول References (Payment Entry Reference):

```
reference_doctype = "Sales Invoice"
reference_name = "رقم الفاتورة"
allocated_amount = 114
```

### 3. في جدول Deductions (Payment Entry Deduction):

```
account = حساب الخصم
cost_center = مركز التكلفة
amount = 4
```

### 4. الحقول المحسوبة تلقائياً (لا تحتاج تعديل):

```
total_allocated_amount = 114 (مجموع allocated_amount من references)
unallocated_amount = 4 (يحسبه النظام تلقائياً)
difference_amount = 0 (يحسبه النظام تلقائياً)
```

### 5. النتيجة:

```
Sales Invoice.outstanding_amount = 0
Sales Invoice.status = "Paid"
```

## الخلاصة

**الحقول التي تملأها:**
1. `paid_amount` = 114
2. `received_amount` = 114
3. `references[0].allocated_amount` = 114
4. `deductions[0].amount` = 4

**النتيجة:** الفاتورة مسددة بالكامل ✅

