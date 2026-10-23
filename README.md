# OTP Rate Limit Bypass — Local PoC

إثبات مفهوم تعليمي يوضح ضعف ربط حد محاولات OTP بهوية المصدر وحدها، ويقارنه بربط الحد بالحساب والتحدّي. يعمل على Python 3.10+ داخل نموذج محلي دون شبكة أو مكتبات خارجية.

## التشغيل على Termux

```bash
pkg install python git
git clone https://github.com/khdertaysh1/otp-rate-limit-bypass.git
cd otp-rate-limit-bypass
python poc.py
```

إذا عندك المستودع مسبقاً، نفّذ `git pull` داخله ثم `python poc.py`. على الكمبيوتر استخدم Python 3.10+؛ قد يكون الأمر `python3`.

## ماذا يثبت؟

```text
#   Source        Vulnerable            Fixed
1   source-A      INVALID_OTP           INVALID_OTP
2   source-A      INVALID_OTP           INVALID_OTP
3   source-A      INVALID_OTP           INVALID_OTP
4   source-A      RATE_LIMITED          RATE_LIMITED
5   source-B      INVALID_OTP           RATE_LIMITED
```

في الرابعة يُمنع المصدر A. تغيير هوية المصدر إلى B في الخامسة يسمح بتقييم محاولة إضافية في الضعيفة، بينما تبقى المُصلحة مقفلة. `INVALID_OTP` يعني أن الرمز فُحص وكان خاطئاً، وليس نجاح تسجيل دخول. المحاولات الخمس تستخدم رمزاً خاطئاً ثابتاً؛ لا تثبت الاستحواذ على حساب.

## جرّب بيدك

```bash
python poc.py --interactive --mode vulnerable
```

اكتب كل أمر وحده ولاحظ متى يبدأ المنع، ثم أثر تغيير هوية المصدر:

```text
check source-A 000000
check source-A 000000
check source-A 000000
check source-A 000000
check source-B 000000
quit
```

كرّر نفس الخطوات في المُصلحة:

```bash
python poc.py --interactive --mode fixed
```

أمر `issue` يصدر تحدّياً جديداً ويلغي القديم مع إبقاء عدّاد الحساب. أمر `reset` يمسح حالة النموذج كاملة. الحساب الوهمي ثابت `alice@example.test`، والرمز التعليمي المعلن `123456`. جرّبه بعد التصفير لفهم النجاح ومنع إعادة استخدام التحدّي؛ ليست هذه بيانات اعتماد حقيقية.

## الدليل والاختبارات

```bash
python poc.py --json > evidence.json
python -m unittest discover -s tests -v
```

الدليل يسجل هل جرى تقييم الرمز أم رُفضت المحاولة قبله. الاختبارات تتحقق من تغيير المصدر، وميزانية الحساب عبر إعادة الإصدار، وحدّ التحدّي، وانتهاء الصلاحية ومنع إعادة الاستخدام.

## سبب الضعف والإصلاح

الضعيفة تستخدم هوية المصدر وحدها كمفتاح للعدّاد: ثلاث محاولات خلال 60 ثانية. المُصلحة تطبّق عدّاداً للحساب مشتركاً بين المصادر: ثلاث محاولات خلال 60 ثانية، مع حد ثابت ثلاث محاولات لكل تحدٍّ خلال عمره. ينتهي التحدّي بعد 300 ثانية ويُستهلك عند النجاح؛ إعادة الإصدار لا تمسح حد الحساب.

في الإنتاج يلزم تخزين ذري مشترك للعدّادات، وتنظيف وانتهاء صلاحية للمفاتيح، وحماية إصدار الرموز وإعادة إرسالها، وهوية حساب موثوقة ورموز عشوائية وتخزين مناسب. وازن حد الحساب مع مخاطر إقفاله بإساءة الاستخدام. النموذج أحادي العملية وذاكرته مؤقتة، وليس خدمة مصادقة جاهزة.

## نطاق الإثبات

هذا نموذج مستقل للفكرة التي نوقشت سابقاً، **وليس إعادة تنفيذ موثقة لخادم بنك أو إثباتاً لثغرة حالية فيه**. أسماء المصادر رموز داخل الذاكرة؛ لا توجد بروكسيات أو HTTP أو عناوين أهداف أو تخمين لرموز حقيقية. النتائج تثبت سلوك النموذج فقط، ولا تحمل تصنيف خطورة أو CVE أو ادعاء قبول تقرير أو استحواذ على حساب.

الملف `PROFILE.md` الموجود سابقاً محفوظ دون تعديل.

## English

Standalone offline PoC for source-only OTP rate limiting. Run `python poc.py`, use `--json` for evidence or `--interactive --mode fixed` for manual attempts. Python 3.10+ standard library only. Changing source identity reopens evaluation in the vulnerable model; account-bound and challenge-bound budgets prevent it in the fixed model. Reissue retains the account budget; challenges expire and are single-use after success. No network, proxies, real targets or actual OTP guessing. This is not a verified reproduction of a bank implementation or proof of account takeover.
