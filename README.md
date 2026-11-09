# Pratik's Paletta

A simple video library built with Python and Django. Upload videos, tag them, find them again, and download them.

It's a small prototype I built to learn Django, inspired by [Paletta](https://www.paletta.io).

## What you can do

- **Upload** several videos at once, with a progress bar
- **Tag** videos (e.g. `lecture, demo`) and filter the library by tag
- **Play** videos in the browser
- **Edit** a video's title and tags
- **Select** several videos to download as a ZIP or delete together
- **Delete** videos (unused tags are tidied up automatically)

## How to run it on your computer

You only need to do steps 1 and 2 once.

### 1. Install Python

Download and install Python 3.12 or newer from [python.org/downloads](https://www.python.org/downloads/).

On Windows, tick **"Add Python to PATH"** on the first screen of the installer.

### 2. Download this project

On this GitHub page, click the green **Code** button, then **Download ZIP**. Unzip it somewhere easy to find, such as your Desktop.

### 3. Open a terminal in the project folder

- **Mac:** open the **Terminal** app, type `cd ` (with a space after it), drag the project folder into the window, and press Enter.
- **Windows:** open the project folder, click the address bar at the top, type `cmd`, and press Enter.

### 4. Set it up (first time only)

Copy and paste these lines into the terminal, one at a time, pressing Enter after each.

**Mac:**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

**Windows:**

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
```

### 5. Start the app

**Mac:**

```bash
source venv/bin/activate
python manage.py runserver
```

**Windows:**

```bat
venv\Scripts\activate
python manage.py runserver
```

Then open **http://127.0.0.1:8000** in your web browser.

To stop the app, go back to the terminal and press **Ctrl + C**. Next time, just repeat step 5.

## Having trouble?

- **"python not found"**: on Mac use `python3` instead of `python`. On Windows, reinstall Python and tick "Add Python to PATH".
- **"No module named django"**: run the `activate` line from step 5 again, then try once more.
- **The page won't load**: check the terminal is still running `runserver` and that you're using the address above.

## For developers

**Run the tests**

```bash
python manage.py test
```

**Admin panel** (optional): run `python manage.py createsuperuser`, then go to http://127.0.0.1:8000/admin.

**Built with:** Python, Django 6.1, SQLite, plain HTML/CSS/JavaScript.

**Project layout**

```
config/     Settings and main URL setup
library/    The app: models, views, forms, templates, styles, tests
media/      Uploaded videos (not stored in git)
```

**Design notes**

- Videos are stored as files on disk; the database only holds their paths, so moving storage to S3 later is a settings change.
- Tags are their own table linked to videos, so filtering is fast and tags can't be duplicated by typos or capitals.
- Uploads use `XMLHttpRequest` so the browser can report real upload progress.
- ZIP downloads are built in a temporary file and streamed, rather than held in memory.
