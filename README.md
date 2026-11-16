# PlateSafe

PlateSafe helps diners with severe food allergies share their allergen requirements with restaurant kitchens through digital Chef Cards and QR codes.

**Phase 1: Account Feature** (IT317, Despues, Charlz David T.)

## Tech Stack
- Django (full stack, Django templates)
- PostgreSQL (Supabase)

## User Roles
- **Diner**: manages allergen profile, Chef Cards, QR code, emergency contacts
- **Kitchen Staff**: scans QR codes, reviews safety checklists, verifies dishes

## Features
- Registration with validation (required fields, email format, unique username/email, password confirmation)
- Login/logout with error messages; protected pages via `@login_required`
- Role-based dashboards; users cannot open another role's dashboard
- Profile view and edit (name, email, contact number, photo)

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then fill in your Supabase credentials
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8080
```