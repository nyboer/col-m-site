# col-m.us — Automated Site Builder

Every time the GitHub Action runs, it:
1. Reads `files.txt` in this repo to find your Google Drive file IDs
2. Downloads each event's `.txt` file + poster image directly from Drive
3. Rebuilds `index.html` from the template
4. Commits the result back to this repo
5. GitHub Pages serves it at col-m.us

No Google Cloud account, no API keys, no subscriptions required — your Drive files just need to be set to "Anyone with the link can view."

---

## One-time setup (about 20 minutes)

### 1. Create a GitHub repo

- Go to github.com → New repository → name it `col-m` (or anything)
- Make it **public** (required for free GitHub Pages)
- Upload all the files from this folder into it

### 2. Enable GitHub Pages

- Go to your repo → **Settings** → **Pages**
- Source: **Deploy from a branch**
- Branch: `main` / root (`/`)
- Save. GitHub will give you a `YOUR-USERNAME.github.io/repo-name` URL.

### 3. Point col-m.us to GitHub Pages

In your Dreamhost DNS panel, add these records:

| Type  | Name | Value                   |
|-------|------|-------------------------|
| A     | @    | 185.199.108.153         |
| A     | @    | 185.199.109.153         |
| A     | @    | 185.199.110.153         |
| A     | @    | 185.199.111.153         |
| CNAME | www  | YOUR-USERNAME.github.io |

Then in your repo → **Settings** → **Pages** → **Custom domain** → enter `col-m.us` and save.
Check "Enforce HTTPS" once it propagates (can take a few hours to a day).

### 4. Make your Drive files public

For each file (event .txt files and poster images):

- Right-click the file in Drive → **Share** → **Change to anyone with the link**
- Click **Copy link** — the URL looks like:
  `https://drive.google.com/file/d/1A2B3C4D5E6F7G8H9I0J/view`
- Paste the full URL directly — no need to extract the ID

### 5. Fill in files.txt

Open `files.txt` in this repo and replace the placeholder IDs with your real ones.
List events in the order you want them on the page — most recent first.

```
apr-2025.txt          https://drive.google.com/file/d/1A2B3C4D5E6F7G8H9I0J/view?usp=sharing
poster-apr-2025.jpg   https://drive.google.com/file/d/1K2L3M4N5O6P7Q8R9S0T/view?usp=sharing

mar-2025.txt          https://drive.google.com/file/d/1U2V3W4X5Y6Z7A8B9C0D/view?usp=sharing
poster-mar-2025.jpg   https://drive.google.com/file/d/1E2F3G4H5I6J7K8L9M0N/view?usp=sharing
```

### 6. Test it

- Go to your repo → **Actions** → **Build & Deploy Site** → **Run workflow**
- Watch the logs — it should download your files and commit a new `index.html`

---

## Your ongoing workflow

Each month:

1. Create a new `.txt` file in Google Drive for the event (see format below)
2. Upload the poster image to Google Drive
3. Set both files to "Anyone with the link can view"
4. Add two lines to `files.txt` in the repo (the .txt and the image), at the top
5. The Action runs automatically every Monday at noon, or trigger it manually

---

## Event .txt file format

Each event is a plain text file in Google Drive with four sections
separated by blank lines:

```
April 2025 — The Luggage Store Gallery

Saturday, April 19, 2025

A rare Bay Area appearance from Limpe Fuchs, pioneer of European
free improvisation, joined by two Bay Area stalwarts.
Doors 7:30pm | Show 8pm | Cover $15 sliding scale
```

That's it:
1. **Title** — shown as the event heading
2. **Date** — shown below the title
3. **Description** — can be as many lines as you want

The poster image is matched to the .txt by their order in `files.txt`
(first .txt pairs with first image, second with second, etc.).

---

## Changing the schedule

Edit `.github/workflows/deploy.yml` and change the cron line:

```yaml
- cron: "0 12 * * 1"   # Every Monday at noon UTC
- cron: "0 18 * * 5"   # Every Friday at 6pm UTC
- cron: "0 0 1 * *"    # First day of every month
```

Use [crontab.guru](https://crontab.guru) to build your own schedule.
