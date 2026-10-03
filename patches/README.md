# Fix: Quazar login "Invalid credentials"

This patch is for **Balastov/Quazar-Messager** (quazar-msg.ru).
The Cloud Agent was attached to BadWordsBot and cannot push to Quazar-Messager.

## Apply

```bash
cd Quazar-Messager
git apply ../BadWordsBot/patches/quazar-messager-auth-email-fix.patch
# or copy files from patches/quazar-messager-files/
```

## What was wrong

1. On production, `m0000nspe1111@yandex.ru` was **not in the database** when checked —
   registration of that email succeeded. Likely a Postgres volume wipe after redeploy;
   the browser still autofilled an old password → `Invalid credentials`.
2. Email matching was **case-sensitive** for the local part (`Alice@x.com` ≠ `alice@x.com`),
   so login could fail even for existing users.

## Fix contents

- Normalize email (trim + lowercase) on register/login
- Case-insensitive lookup for legacy rows
- Russian auth error messages
- `POST /users/me/password` to change password when logged in
