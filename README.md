> **Moved:** this project now lives in [pseigne/tldr-syllabus](https://github.com/pseigne/tldr-syllabus) under `backend/`, with full history. This repository is archived.

# Syllabus analyzer API

Flask API for the portfolio Syllabus Analyzer. Deploy the `render.yaml` blueprint on Render's Free web-service plan; no paid instance or payment method is required. The service sleeps when idle, so the frontend displays a startup message while it wakes.

## Configuration

Set `OPENAI_API_KEY` to a replacement Neon-funded key directly in Render. Never commit a key or put it in frontend configuration. Set `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` from an Upstash Free Redis database. Render generates `RATE_LIMIT_SALT`; preserve it across deploys. `ALLOWED_ORIGINS` defaults to `https://pierceseigne.com`.

PDF uploads are limited to 10 MB and 30 pages. A Redis Lua transaction reserves an attempt before calling OpenAI: three per IP per UTC day and twenty overall. Only a salted hash of the IP is stored, expiring after two days. Redis failure blocks uploads. Only one analysis runs at a time. Temporary uploaded files are deleted after each request; document contents are sent to OpenAI for analysis. Example syllabi work independently of this service.

Render and Upstash must remain on their Free plans. OpenAI usage is funded separately by Neon and is not included in Render hosting. The upload caps limit requests; enforce the organization's desired API budget in its OpenAI project as well.

## Development

Use Python 3.12, install `requirements.txt`, then run `python -m unittest discover -s tests -v`. Tests mock AI calls and do not incur usage. Start locally with `python app.py`. Production uses Gunicorn, not Flask's debug server. `/health` reports whether required settings are present; `/upload` is the sole analysis endpoint.

Point `api.pierceseigne.com` at Render's assigned service hostname using the DNS instructions in its custom-domain screen. Until that record exists, build the frontend with `VITE_SYLLABUS_API_URL` set to the assigned `https://…onrender.com` URL.
