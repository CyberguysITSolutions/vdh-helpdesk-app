#!/usr/bin/env python3
"""
Password Hash Generator for VDH Crater Service Center
Run this script to generate secure password hashes
"""

try:
    from werkzeug.security import generate_password_hash
except ImportError:
    print("ERROR: werkzeug is not installed!")
    print("Install it with: pip install werkzeug")
    exit(1)

def hash_password(password):
    """Generate secure scrypt hash"""
    return generate_password_hash(password, method='scrypt')

print("=" * 70)
print(" PASSWORD HASH GENERATOR - VDH Crater Service Center")
print("=" * 70)
print()

# =======================================================================
# EDIT THESE PASSWORDS
# =======================================================================
# Replace 'CURRENT_PASSWORD' with the actual current password for gclarke
# The jblack password is already set
users = {
    'gclarke': 'Crater@2026',  # ← Change this
    'jblack': 'Crater@2026',                    # ← This is already correct
}
# =======================================================================

print("Generating secure password hashes...")
print()

sql_statements = []

for username, password in users.items():
    if password == 'CURRENT_PASSWORD':
        print(f"⚠️  WARNING: {username} - Please set the password in this script first!")
        print(f"   Edit line 20 and replace 'CURRENT_PASSWORD' with actual password")
        print()
        continue
    
    # Generate hash
    hashed = hash_password(password)
    
    # Create SQL
    sql = f"UPDATE dbo.Users SET password_hash = '{hashed}' WHERE username = '{username}';"
    sql_statements.append(sql)
    
    print(f"✅ {username}")
    print(f"   Password: {password}")
    print(f"   Hash: {hashed[:50]}...")
    print()

if sql_statements:
    print("=" * 70)
    print(" COPY AND RUN THESE SQL STATEMENTS IN AZURE")
    print("=" * 70)
    print()
    print("USE [helpdesk-db];")
    print("GO")
    print()
    for sql in sql_statements:
        print(sql)
    print()
    print("GO")
    print()
    print("-- Verify the updates")
    print("SELECT username, LEFT(password_hash, 30) + '...' AS hash_preview")
    print("FROM dbo.Users;")
    print()
    print("=" * 70)
    print()
    print("📋 Next Steps:")
    print("1. Copy the SQL above")
    print("2. Go to Azure Portal → helpdesk-db → Query Editor")
    print("3. Paste and run the SQL")
    print("4. Test login with each user")
    print("5. Verify no more 'plain text password' warnings in logs")
    print()
    print("✅ Passwords will be securely hashed!")
else:
    print()
    print("❌ No SQL generated. Please set passwords in the script first.")
    print()
