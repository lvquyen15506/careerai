# Deploy to Render - Student Job Platform (CareerAI)

This document describes a ready-to-run workflow to deploy this Django app to Render (https://render.com).

## Summary
- App type: Python / Django
- WSGI server: Gunicorn (Procfile/start command provided)
- DB: external MySQL or Render Managed Postgres
- Media (avatars): AWS S3 / DigitalOcean Spaces / Cloudinary (recommended: S3 or Cloudinary)

---

## Files added
- `Procfile` - web startup command using Gunicorn
- `runtime.txt` - Python runtime hint
- `requirements.txt` updated with `gunicorn`, `django-storages[boto3]`, `boto3`, `psycopg2-binary`
- `student_job_platform/settings.py` patched to enable S3 when `USE_S3=True` env var is set

---

## Steps on Render

1. Push your repo to GitHub (or connect repo in Render).
2. Create a new **Web Service** in Render and connect your repo/branch.
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn student_job_platform.wsgi:application --bind 0.0.0.0:$PORT --workers 3`
3. Set Environment Variables (Render dashboard → Environment)
   - `DJANGO_SECRET_KEY` = (your secret key)
   - `DJANGO_DEBUG` = `False`
   - `ALLOWED_HOSTS` = `your-app.onrender.com` (or comma-separated hosts)
   - Database: either provide `DB_*` vars (if using external MySQL) or attach a Render Postgres and provide `DB_*` or `DATABASE_URL`.

### If using AWS S3 (recommended for media)
Set these env vars:
```
USE_S3=True
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=ap-southeast-1
AWS_S3_CUSTOM_DOMAIN=cdn.example.com   # optional, if you configure CDN
```
After setting `USE_S3=True`, the `settings.py` will set `DEFAULT_FILE_STORAGE` and `STATICFILES_STORAGE` to use S3.

### If using Cloudinary
- Install `django-cloudinary-storage` (not included by default) and set `CLOUDINARY_URL` in env.

4. Deploy the service.

5. Once deployed, run one-off commands (Render Dashboard → Shell) to set up DB and static files:
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser   # optional
```

6. Media migration (if you have existing `media/` locally):
- Use AWS CLI to upload:
```bash
aws s3 sync media/ s3://your-bucket-name/media/ --acl private
```

---

## Recommended Security & Production settings
- `DJANGO_DEBUG=False`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`
- Use strong `DJANGO_SECRET_KEY` and rotate if exposed
- Do not store user portal passwords in plain text

---

## Troubleshooting
- If collectstatic uploads fail: verify AWS keys and bucket policy (write access).
- If DB connection fails: ensure network access and correct host/port; for managed DB check firewall/allowlist.
- Logs: use Render dashboard logs to inspect Gunicorn/Django errors.

---

If you want, I can now:
- Run a patch to add Sentry/monitoring hooks, or
- Add a Cloudinary option and helper functions to migrate existing media, or
- Prepare a Render YAML service file if you use `render.yaml` deployment.

Tell me which next step you want me to perform.