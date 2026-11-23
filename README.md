# PlateSafe

PlateSafe helps diners with severe food allergies share their allergen requirements with restaurant kitchens through digital Chef Cards and QR codes.

**IT317 · Despues, Charlz David T. · G6**

## Tech Stack
- Django (full stack, Django templates)
- PostgreSQL (Supabase)

## User Roles
- **Diner**: manages allergen profile, Chef Cards, QR code, emergency contacts
- **Kitchen Staff**: views Chef Cards, manages the allergen catalog and kitchen rule library, reviews safety checklists

## Phase 1: Account Feature
- Registration with validation (required fields, email format, unique username/email, password confirmation)
- Login/logout with error messages; protected pages via `@login_required`
- Role-based dashboards; users cannot open another role's dashboard
- Profile view and edit (name, email, contact number, photo)

## Phase 2 (Core Feature): Allergen Profile & Chef Card Builder

PlateSafe turns a diner's allergen profile into a Chef Safety Card that kitchen staff can read at a glance.

**Diner**
- Builds an allergen profile: major or custom allergens, each with a severity (Mild, Moderate, Severe, Anaphylactic), plus dietary notes and medical flags.
- Creates Chef Cards from the profile, picks optional kitchen rules and writes a note to the chef.
- Required cross-contamination rules are added automatically for Severe and Anaphylactic allergens and can't be removed.
- Activates one card at a time (activating a new card archives the old one), previews and prints it, edits, archives or deletes cards.
- Changing an active card's allergens, severities or rules creates a new version and returns it to draft.

**Kitchen Staff**
- Views every Chef Card in the system (read-only).
- Manages the major allergen catalog and the preparation rule library.

All data is stored in PostgreSQL (Supabase). Every page requires login, and diners can only see and change their own records.

### Main pages
| URL | Role | What |
| --- | --- | --- |
| `/allergens/` | Diner | Allergen profile (add, edit, remove) |
| `/chef-cards/` | Diner | My Chef Cards |
| `/chef-cards/new/` | Diner | Chef Card builder |
| `/chef-cards/all/` | Kitchen | All Chef Cards |
| `/chef-cards/rules/` | Kitchen | Preparation rule library |
| `/allergens/catalog/` | Kitchen | Allergen catalog |

## Setup
```bash
git clone https://github.com/RiasWyrtalius/PlateSafe-Despues-Charlz-G6.git
cd PlateSafe-Despues-Charlz-G6
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then fill in your Supabase credentials
python manage.py migrate
python manage.py seed_allergens
python manage.py seed_rules
python manage.py createsuperuser
python manage.py runserver 8080
```

## Testing the core feature
1. Register a **Diner** account and log in.
2. Dashboard → **Add allergen** → add Peanuts as Anaphylactic.
3. **Chef Cards → New Chef Card**: the required rules are already locked in → create → **Activate this card**.
4. Edit the card's rules: it becomes version 2 and goes back to draft.
5. Register a **Kitchen** account: the dashboard links to All Chef Cards and the Rule library.