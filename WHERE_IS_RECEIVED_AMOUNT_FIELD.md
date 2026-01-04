# أين يوجد حقل received_amount؟

## معلومات الحقل

من قاعدة البيانات:
```
fieldname: received_amount
label: "Received Amount"
fieldtype: Currency
hidden: 0 (ظاهر في الواجهة)
read_only: 0 (قابل للتعديل)
reqd: 1 (إجباري)
print_hide: 1 (مخفي في الطباعة فقط)
```

## موقع الحقل في الواجهة

**في Payment Entry:**

1. قسم "Payment Amounts" (section_break في payment_amounts_section)

2. في نفس الصف (row) مع `paid_amount`، لكن في عمود منفصل (column_break_21)

3. الترتيب:
   ```
   [Paid Amount]        |  [Received Amount]  ← هنا!
   [Paid Amount After Tax] | [Received Amount After Tax]
   [Source Exchange Rate] | [Target Exchange Rate]
   [Base Paid Amount]    | [Base Received Amount]
   ```

## ملاحظة مهمة

من الكود في `set_received_amount()` (سطر 977-983):

**إذا كانت العملات متطابقة:**
```python
if self.paid_from_account_currency == self.paid_to_account_currency:
    self.received_amount = self.paid_amount  # يتم تعيينه تلقائياً
```

**النتيجة:**
- إذا كانت عملة `paid_from` = عملة `paid_to`
- فإن `received_amount` = `paid_amount` تلقائياً
- قد لا تحتاج لتعديله يدوياً

## الخلاصة

**الحقل موجود في:**
- قسم "Payment Amounts"
- في العمود الثاني (بعد Paid Amount)
- بجانب Paid Amount

**إذا لم تراه:**
- تأكد أنك في Payment Entry (وليس Payment Request)
- تأكد أنك في قسم "Payment Amounts"
- إذا كانت العملات متطابقة، قد يكون مساوي لـ paid_amount تلقائياً

