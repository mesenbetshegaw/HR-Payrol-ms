"""
Fix Django 5.1.4 Python 3.14 compatibility bug.
Run with BOTH python interpreters:
  py fix_django_py314.py
  .\venv\Scripts\python.exe fix_django_py314.py
"""
import sys
import os

print(f"Python: {sys.version}")
print(f"Executable: {sys.executable}")

# Find Django's context.py
try:
    import django.template.context as m
    context_path = m.__file__
    print(f"context.py: {context_path}")
except ImportError:
    print("ERROR: Django not installed for this Python.")
    sys.exit(1)

# Read the file
with open(context_path, "r", encoding="utf-8") as f:
    content = f.read()

# The broken code
old_code = """    def __copy__(self):
        duplicate = copy(super())
        duplicate.dicts = self.dicts[:]
        return duplicate"""

# The fixed code
new_code = """    def __copy__(self):
        duplicate = self.__class__.__new__(self.__class__)
        duplicate.__dict__.update(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(context_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ Python 3.14 fix applied to context.py!")
elif new_code in content:
    print("✅ Already patched — no action needed.")
else:
    print("⚠️  Pattern not found — Django version may differ.")
    print("   Check context.py manually at:", context_path)

# Now verify Django check works
print("\nRunning Django system check...")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
try:
    import django
    django.setup()
    from django.core.management import call_command
    call_command("check", "--skip-checks=security")
    print("✅ Django check passed!")
except Exception as e:
    print(f"❌ Django check error: {e}")
