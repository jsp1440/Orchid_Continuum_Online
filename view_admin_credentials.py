"""
View your admin credentials
Run this to see what email/password you need to use
"""
import os

print("\n" + "="*60)
print("ADMIN LOGIN CREDENTIALS")
print("="*60)

admin_email = os.environ.get('ADMIN_EMAIL')
admin_password = os.environ.get('ADMIN_PASSWORD')

if admin_email:
    print(f"\nEmail: {admin_email}")
else:
    print("\nEmail: (not set - you can leave blank)")

if admin_password:
    print(f"Password: {admin_password}")
else:
    print("Password: (NOT SET - admin login disabled!)")

print("\n" + "="*60)
print("Login at: /admin/login")
print("="*60 + "\n")
