# الخطوات الصحيحة المختصرة

## السيناريو
- الفاتورة = 114
- استلمت = 110 (فعلياً)
- تريد خصم = 4
- تريد: الفاتورة مسددة بالكامل

## الحل الصحيح (من البيانات الفعلية ACC-PAY-2026-00001)

### الخطوات:

1. **في Payment Entry:**

   ```
   Paid Amount = 114
   Received Amount = 114
   ```

2. **في جدول References:**

   ```
   Allocated Amount = 114  (مبلغ الفاتورة الكامل)
   ```

3. **في جدول Deductions:**

   ```
   Amount = 4
   ```

4. **النتيجة:**
   - النظام سيحسب تلقائياً:
     - `unallocated_amount = 4`
     - `difference_amount = 0`
   - الفاتورة ستكون "Paid" (مسددة بالكامل)

## الفهم الصحيح

### القاعدة:

**لدفع الفاتورة بالكامل:**
```
allocated_amount = invoice_grand_total
```

**المعادلة (من الكود):**
```
paid_amount = allocated_amount + unallocated_amount + deduction

لكن:
unallocated_amount = paid_amount + deduction - allocated_amount
```

**في حالتك:**
```
114 = 114 + 4 - 4 (unallocated) = 114 ✓
```

## ملاحظة مهمة

**البيانات الفعلية تظهر:**
- `paid_amount = 114` (وليس 110)

**إذا استلمت 110 فعلياً:**
- يجب أن تضع `paid_amount = 114` في النظام
- هذا يعني أنك تدفع 114 (رغم استلامك 110)
- الفرق (4) سيكون في `unallocated_amount`

## الخلاصة

**الخطوات:**
1. `paid_amount = 114`
2. `allocated_amount = 114` (مبلغ الفاتورة)
3. `deduction = 4`
4. النظام سيحسب الباقي تلقائياً

**النتيجة:** الفاتورة مسددة بالكامل ✅

