# col-m.us — Automated Site Builder

Every time the GitHub Action runs, it:
1. Pulls `events.md` + poster images from your Google Drive folder
2. Rebuilds `index.html` from the template
3. Commits the result back to this repo
4. GitHub Pages serves it at col-m.us

---

## One-time setup (about 30 minutes)

### 1. Create a GitHub repo

- Go to github.com → New repository → name it `col-m` (or anything)
- Make it **public** (required for free GitHub Pages)
- Upload all these files into it

### 2. Enable GitHub Pages

- Go to your repo → **Settings** → **Pages**
- Source: **Deploy from a branch**
- Branch: `main` / root (`/`)
- Save. GitHub will give you a `*.github.io` URL — your custom domain will point here.

### 3. Point col-m.us to GitHub Pages

In your Dreamhost DNS panel (or wherever the domain is managed):

Add these DNS records:

| Type  | Name | Value                  |
|-------|------|------------------------|
| A     | @    | 185.199.108.153        |
| A     | @    | 185.199.109.153        |
| A     | @    | 185.199.110.153        |
| A     | @    | 185.199.111.153        |
| CNAME | www  | YOUR-USERNAME.github.io |

Then in your repo → Settings → Pages → **Custom domain** → enter `col-m.us`.
Check "Enforce HTTPS" once it propagates (can take a few hours).

### 4. Set up Google Drive access

**a) Create a Google Cloud project**
- Go to console.cloud.google.com
- New Project → name it "col-m site"
- Enable the **Google Drive API** (APIs & Services → Enable APIs → search Drive)

**b) Create a Service Account**
- APIs & Services → Credentials → Create Credentials → Service Account
- Name: `col-m-builder`, role: Viewer
- After creation, click the account → Keys → Add Key → JSON
- Download the JSON file — keep it safe, you'll need it in step 6

**c) Share your Drive folder with the service account**
- Create a folder in Google Drive called `col-m-site` (or whatever)
- Right-click → Share → paste the service account email (looks like `col-m-builder@your-project.iam.gserviceaccount.com`)
- Set to **Viewer**

**d) Get the folder ID**
- Open the folder in your browser
- Copy the long ID from the URL: `drive.google.com/drive/folders/THIS-PART-HERE`

### 5. Add GitHub Secrets

In your repo → Settings → Secrets and variables → Actions → New repository secret:

| Secret name                   | Value                                         |
|-------------------------------|-----------------------------------------------|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | The entire contents of the JSON key file      |
| `DRIVE_FOLDER_ID`             | The folder ID from step 4d                    |

### 6. Test it

- Go to your repo → Actions → "Build & Deploy Site" → Run workflow
- Watch the logs — it should download your files and commit a new `index.html`

---

## Your ongoing workflow

Each month, to update the site:

1. **Add the poster image** to your Google Drive folder (e.g. `poster-may-2025.jpg`)
2. **Edit `events.md`** in the Drive folder — add a new event block at the top
3. That's it. The Action runs automatically Monday at noon, or you can trigger it manually.

---

## events.md format

```markdown
## Month YYYY — Venue Name
**Date:** Saturday, Month DD, YYYY
**Artists:** Artist One, Artist Two, Artist Three
**Doors:** 8pm | **Show:** 8:30pm | **Cover:** $10
**Poster:** poster-mon-yyyy.jpg

Optional description paragraph here.

---

## Previous Month YYYY — Venue Name
...
```

- Most recent event goes **first**
- Separate events with `---` on its own line
- Poster filename must exactly match the image file in the Drive folder

---

## Changing the schedule

Edit `.github/workflows/deploy.yml` and change the cron line:

```yaml
- cron: "0 12 * * 1"   # Every Monday at noon UTC
- cron: "0 18 * * 5"   # Every Friday at 6pm UTC
- cron: "0 0 1 * *"    # First day of every month
```

Use [crontab.guru](https://crontab.guru) to build your own schedule.
