# Limousine Management System

أساس نظام ويب لإدارة شركة ليموزين، مبني بـPython 3.12 وDjango 5.2 LTS، مع فصل المسؤوليات وفق Clean Architecture. قاعدة البيانات المعتمدة هي **Oracle Database فقط**، ويجري الاتصال بها عبر `python-oracledb 4.0.2` في Thin mode.

الموجود حاليًا شريحة أولى لإضافة السيارات وعرضها وتعديل نمرة السيارة وإرفاق الصور والملفات. الحفظ يستهدف Oracle فقط ويتطلب إعداد الاتصال وتطبيق الترحيلات. المستخدمون والصلاحيات لم يُنفَّذوا بعد.

## الموجود حاليًا

- واجهة إنجليزية افتراضيًا على `/`، مع تبديل كامل للعربية واتجاه RTL وحفظ اللغة محليًا.
- وضع ليلي ونهاري مع حفظ الاختيار محليًا، وتصميم متجاوب.
- قائمة سيارات بسيطة مرتبة حسب تسلسل إضافتها، مع نموذج إضافة وخانة نمرة السيارة.
- صفحة لكل سيارة لتعديل بياناتها الثابتة وإضافة صور ومستندات خاصة بها. أنواع الملفات المدعومة موضحة بالواجهة، والحد 10 ميجابايت لكل ملف.
- فحص حياة التطبيق على `/health/live/`؛ لا يحتاج قاعدة بيانات.
- فحص جاهزية قاعدة البيانات على `/health/ready/`؛ يعيد `503` عندما لا تكون Oracle مهيأة أو لا يمكن الاتصال بها.
- إعدادات منفصلة للتطوير والاختبارات والإنتاج.
- أوامر تشغيل لـWindows، وDocker لتشغيل خدمة الويب.
- اختبارات لا تحتاج حساب Oracle أو اتصالًا بالإنترنت.

لا توجد بيانات تجريبية في التشغيل، ولا SQLite أو PostgreSQL بديلة. توجد ترحيلة أولى لجداول السيارات والمرفقات، ولم تُطبّق على Oracle حقيقية بعد. عدم إعداد Oracle يسمح بتشغيل صفحة البداية وفحص الحياة محليًا؛ لا يجعل التطبيق جاهزًا لحفظ البيانات.

## تشغيل محلي على Windows

نفّذ الأوامر من جذر المستودع في PowerShell. إذا كان لديك Python 3.12 العادي:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
powershell -ExecutionPolicy Bypass -File scripts/run.ps1 -Command check
powershell -ExecutionPolicy Bypass -File scripts/run.ps1 -Command runserver
```

افتح `http://127.0.0.1:8000/`. لفحص حياة التطبيق استخدم `http://127.0.0.1:8000/health/live/`، ولجاهزية Oracle استخدم `http://127.0.0.1:8000/health/ready/`.

السكربت `scripts/run.ps1` يختار Python من `.venv` أولًا، ثم `.runtime/python` إذا كانت البيئة المحمولة المحلية مجهزة، ثم `python` المتاح في النظام. مجلد `.runtime` محلي وغير متتبّع في Git؛ ليس بديلًا عن تثبيت الاعتمادات عند إعداد جهاز جديد.

يمكن تشغيل أوامر Django مباشرة أيضًا:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver
```

عند غياب إعدادات Oracle، يتجاوز أمر التطوير `runserver` فحص الترحيلات الذي يتطلب الاتصال بها فقط. هذا لا يفعّل قاعدة بديلة ولا يثبت نجاح الاتصال.

## إعداد Oracle

انسخ `.env.example` إلى `.env` مرة واحدة، ثم ضع بيانات اتصال قاعدة Oracle التي أنشأتها فعليًا:

| المتغير | الاستخدام |
| --- | --- |
| `ORACLE_DSN` | وصف الاتصال أو الاسم المعتمد من إعدادات قاعدة Oracle |
| `ORACLE_USER` | مستخدم التطبيق في قاعدة البيانات |
| `ORACLE_PASSWORD` | كلمة مرور مستخدم قاعدة البيانات |
| `ORACLE_CONFIG_DIR` | مسار ملفات إعداد Oracle عند استخدامها؛ اختياري |
| `ORACLE_WALLET_LOCATION` | مسار Wallet إذا كان نوع الاتصال يتطلبها؛ اختياري |
| `ORACLE_WALLET_PASSWORD` | كلمة مرور Wallet عند الحاجة؛ اختياري |

استخدم وصف الاتصال وملفات Wallet الخاصة بقاعدتك، حسب نوع الاتصال المختار. اتصال Thin لا يحتاج تثبيت Oracle Instant Client، لكن خدمة Oracle نفسها يجب أن تكون متاحة ومهيأة للاتصال من جهازك.

بعد اكتمال المتغيرات الثلاثة الأساسية، جرّب `/health/ready/`. يمكن تنفيذ الترحيلات المعرّفة للمشروع بالأمر التالي؛ لن ينفّذ السكربت `migrate` دون إعداد اتصال كامل:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run.ps1 -Command migrate
```

**لا توجد نتيجة اختبار اتصال Oracle أو ترحيلات Oracle ناجحة ضمن هذه الدفعة**؛ يلزم اختبارها على قاعدة حقيقية بعد توفير بيانات الاتصال والصلاحيات المناسبة. لا تحفظ `.env` أو ملفات Wallet أو كلمات المرور في Git.

## الاختبارات والفحص

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run.ps1 -Command check
powershell -ExecutionPolicy Bypass -File scripts/run.ps1 -Command test
```

أو باستخدام Python مباشرة:

```powershell
.\.venv\Scripts\python.exe manage.py test --settings=limousine.config.settings.test
```

اختبارات هذه المرحلة تستخدم `SimpleTestCase` ولا تنشئ قاعدة بيانات. إعدادات الاختبار تستخدم backend غير متصل لمنع الاتصال العرضي؛ ليس محرك قاعدة بيانات ثانيًا للتطبيق، ولا تختبر تخزين السجلات أو ترحيلها إلى Oracle.

## Docker والإنتاج

يمكن تشغيل نسخة الأساس محليًا، بعد تجهيز ملف `.env` من المثال، حتى لو لم تُستكمل إعدادات Oracle:

```powershell
docker compose up --build
```

Compose يشغّل **خدمة الويب فقط** باستخدام Gunicorn وإعدادات التطوير المحلي، ويعرضها على `http://127.0.0.1:8000/` على الجهاز فقط. تعمل صفحة البداية وفحص الحياة دون Oracle، وتبقى الجاهزية `503` عند غياب إعداد الاتصال. لا يُنشئ Compose حاوية Oracle أو حسابًا سحابيًا، ولا ينشر المشروع على الإنترنت. عند تفعيل الاتصال، يلزم أن تكون Oracle الخارجية قابلة للوصول من الحاوية، وأن تكون مسارات Wallet، إن استُخدمت، متاحة لها.

إعداد `Dockerfile` الافتراضي يستخدم إعدادات **الإنتاج**؛ يتجاوز Compose هذا الاختيار بإعدادات التشغيل المحلي. تشغيل الصورة منفردة بإعدادها الافتراضي يتطلب `DJANGO_SECRET_KEY` وإعدادات Oracle و`DJANGO_ALLOWED_HOSTS`. اضبط أيضًا `DJANGO_CSRF_TRUSTED_ORIGINS` وفق عنوان النشر الفعلي عند تجهيز HTTPS.

بعد إعداد متغيرات الإنتاج، نفّذ فحص Django التالي باستخدام بيئة Python المثبت فيها الاعتمادات:

```powershell
.\.venv\Scripts\python.exe manage.py check --deploy --settings=limousine.config.settings.production
```

راجع نتائج الفحص وفق بيئة النشر الفعلية. لا تفعّل خيارات HSTS الخاصة بـ`include_subdomains` و`preload` قبل تأمين HTTPS لجميع النطاقات الفرعية المعنية.

أمر جمع الملفات الثابتة متاح عبر السكربت، ويستخدم `settings.base` لتجميعها مع manifest:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run.ps1 -Command collectstatic
```

**لم يُختبر بناء الصورة أو تشغيل الحاوية في هذه البيئة لأن Docker daemon غير متاح.** وجود ملفات Docker وCompose لا يثبت نجاح تشغيلهما أو اتصال الحاوية بـOracle.

## الوثائق والخطوات التالية

- [حدود الطبقات وقرارات البنية](docs/architecture.md).
- [المتطلبات المفتوحة وترتيب العمل التالي](docs/next-steps.md).

تجهيز النسخ الاحتياطي والتصدير والاسترجاع الخاص بـOracle لم يُنفّذ بعد. جدولة سحب نسخة اللابتوب عبر Windows Task Scheduler مؤجلة للمرحلة الأخيرة.
