import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from accounts.models import User

user, created = User.objects.get_or_create(
    email="messi@hrpayroll.et",
    defaults={
        "first_name": "Messi",
        "last_name": "Admin",
        "role": "ADMIN",
        "is_staff": True,
        "is_superuser": True,
    }
)
user.set_password("8640")
user.is_staff = True
user.is_superuser = True
user.role = "ADMIN"
user.save()

if created:
    print("✅ Superuser messi@hrpayroll.et created (password: 8640)")
else:
    print("✅ Superuser messi@hrpayroll.et updated (password: 8640)")

print("   Django Admin: http://127.0.0.1:8000/admin/")
print("   API Login:    http://127.0.0.1:8000/api/v1/auth/login/")
