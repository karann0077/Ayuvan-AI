# AYUVAN legal pages

This is a static GitHub Pages site with three public pages:

- `/privacy/` — Privacy Policy
- `/terms/` — Terms of Service
- `/data-deletion/` — User Data Deletion Instructions

## Before publishing

Edit `assets/config.js`. Replace every bracketed placeholder with AYUVAN's real legal entity name, registered business address, and a working email inbox. Do not publish with placeholders.

Have an Indian privacy/healthcare lawyer review these documents before a patient-facing launch. The policy is tailored to AYUVAN's described product, but it is not legal advice or a claim of legal compliance.

## GitHub Pages deployment

1. Push this project to GitHub. The included workflow deploys only this `legal-pages` folder.
2. In GitHub: **Settings → Pages → Build and deployment → Source**, select **GitHub Actions**.
3. Open the repository’s **Actions** tab and wait for the “Deploy legal pages” workflow to complete.
4. GitHub will publish at `https://YOUR-GITHUB-USERNAME.github.io/YOUR-REPOSITORY-NAME/`.

Use these URLs in Meta:

```text
https://YOUR-GITHUB-USERNAME.github.io/YOUR-REPOSITORY-NAME/privacy/
https://YOUR-GITHUB-USERNAME.github.io/YOUR-REPOSITORY-NAME/terms/
https://YOUR-GITHUB-USERNAME.github.io/YOUR-REPOSITORY-NAME/data-deletion/
```

Confirm all three pages load publicly before entering the URLs in Meta.
