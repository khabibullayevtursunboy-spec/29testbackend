# School Test System — Django backend

O'qituvchi test joylaydi, o'quvchi istalgan kompyuterdan testni ishlaydi, natijalar o'qituvchi panelida ko'rinadi.

Stack: Django 5 + Django REST Framework + PostgreSQL (Render) / SQLite (lokal).

## Lokal ishga tushirish (Windows)

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8000
```

API: http://127.0.0.1:8000/api/  — Admin: http://127.0.0.1:8000/admin/

## Render'ga joylash

1. Loyihani GitHub'ga yuklang (`.gitignore` tayyor).
2. Render → New → **Blueprint** → repoyingizni tanlang (`render.yaml` avtomatik o'qiladi, PostgreSQL ham yaratiladi).
   Yoki qo'lda: Web Service → Build: `./build.sh`, Start: `gunicorn config.wsgi:application`.
3. Environment o'zgaruvchilari:
   - `FRONTEND_URLS` = Vercel manzilingiz (masalan `https://my-app.vercel.app`) — bir nechta bo'lsa vergul bilan
   - `TEACHER_CODE` = o'qituvchilar ro'yxatdan o'tishi uchun maxfiy kod
   - `SECRET_KEY`, `DATABASE_URL`, `DEBUG=False` — render.yaml'da tayyor
4. Admin yaratish: Render → Shell → `python manage.py createsuperuser`
5. Vercel'da frontend env: API manzili = `https://<sizning-servis>.onrender.com/api`

> Render bepul rejada servis 15 daqiqa ishlatilmasa uxlab qoladi, birinchi so'rov ~30-60 soniya olishi mumkin.

## Autentifikatsiya

Token: har bir so'rovda `Authorization: Token <token>` sarlavhasi.

| Metod | URL | Tavsif |
|---|---|---|
| POST | `/api/auth/register/` | `{username, password, full_name, role: "student"/"teacher", school_class, teacher_code}` → `{token, user}` |
| POST | `/api/auth/login/` | `{username, password}` → `{token, user}` |
| POST | `/api/auth/logout/` | tokenni o'chiradi |
| GET | `/api/auth/me/` | joriy foydalanuvchi |

`teacher_code` faqat `role="teacher"` uchun kerak (agar `TEACHER_CODE` env o'rnatilgan bo'lsa).

## Testlar

| Metod | URL | Kim | Tavsif |
|---|---|---|---|
| GET | `/api/tests/` | hamma | O'qituvchi: o'z testlari. O'quvchi: e'lon qilinganlari (`already_taken` bilan) |
| POST | `/api/tests/` | o'qituvchi | Test yaratish (savollar va variantlar bilan) |
| GET | `/api/tests/<id>/` | hamma | O'qituvchi: to'g'ri javoblar bilan. O'quvchi: to'g'ri javobsiz |
| PUT/PATCH | `/api/tests/<id>/` | o'qituvchi | Tahrirlash (natija bor testda savollarni o'zgartirib bo'lmaydi) |
| DELETE | `/api/tests/<id>/` | o'qituvchi | O'chirish |
| POST | `/api/tests/<id>/submit/` | o'quvchi | Javob yuborish → natija (har o'quvchi bir marta) |
| GET | `/api/tests/<id>/results/` | o'qituvchi | Shu test bo'yicha barcha natijalar |

Test yaratish namunasi:

```json
{
  "title": "Algebra 1-chorak",
  "subject": "Matematika",
  "description": "",
  "duration_minutes": 30,
  "is_published": true,
  "questions": [
    {
      "text": "2 + 2 = ?",
      "points": 1,
      "choices": [
        {"text": "3", "is_correct": false},
        {"text": "4", "is_correct": true}
      ]
    }
  ]
}
```

Javob yuborish namunasi:

```json
{"answers": [{"question": 12, "choice": 45}, {"question": 13, "choice": null}]}
```

## O'qituvchi paneli

| Metod | URL | Tavsif |
|---|---|---|
| GET | `/api/students/` | o'quvchilar ro'yxati (`?school_class=9-A`), ishlagan testlari soni va o'rtacha foiz |
| GET | `/api/students/<id>/` | o'quvchi va uning barcha natijalari |
| GET | `/api/attempts/` | barcha natijalar (`?test=<id>`, `?student=<id>`) |
| GET | `/api/attempts/<id>/` | batafsil: har bir savolga qaysi javob berilgan |

O'quvchi `/api/attempts/` orqali faqat o'z natijalarini ko'radi.
