# Paletta-Lite

A small Django prototype of a video library, built as a hands-on way to learn Django. It supports uploading several videos at once, tagging them, filtering the library by tag, and downloading files.

It is a prototype, not production code.

## Features

- Upload multiple videos in one go
- Apply comma-separated tags to every file in an upload (tags are normalised and de-duplicated)
- Filter the library by tag (`/?tag=lecture`)
- Play videos in the browser
- Download videos through a dedicated view, so permission checks can be added later
- Django admin for managing videos and tags
- Automated test for tag filtering

## Tech stack

- Python 3
- Django 6.1
- SQLite (development database)
- Local file storage for uploads (`media/`)

## Getting started

```bash
git clone https://github.com/Raip036/palleta-lite.git
cd palleta-lite

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser   # optional, for /admin
python manage.py runserver
```

Then open http://127.0.0.1:8000/.

| URL | What it does |
| --- | --- |
| `/` | Video library with tag filter |
| `/upload/` | Upload one or more videos with tags |
| `/download/<id>/` | Download a video |
| `/admin/` | Django admin |

## Running the tests

```bash
python manage.py test
```

## Project structure

```
config/     Project settings and root URL configuration
library/    The app: models, views, forms, templates, tests
  models.py     Tag and Video (many-to-many)
  forms.py      Multi-file upload form
  views.py      List/filter, upload, download
  templates/    HTML templates
media/      Uploaded files (git-ignored)
```

## Design notes

- `Video.file` is a `FileField`, so the database stores only a path and the file lives in `MEDIA_ROOT`, which makes swapping in S3 later straightforward.
- Tags are a separate model with a many-to-many relation, so filtering is a proper join and tags can't be duplicated by typos or casing.
- `prefetch_related("tags")` avoids N+1 queries on the library page.
- Downloads go through a streamed view rather than a direct media link, so access control can be added in one place.
