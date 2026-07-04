# Deployment Guide for Bidwan Residential College Website

## Recommended hosting setup

1. **Static public site**
   - Host `index.html`, `about.html`, `courses.html`, `course-details.html`, `gallery.html`, `contact.html`, and `addmission.html` on a static host.
   - Recommended hosts:
     - Netlify
     - Vercel
     - Cloudflare Pages
     - GitHub Pages

2. **Python backend / admin API**
   - Keep the admin portal and API on a separate server or private service.
   - Recommended hosts:
     - Render
     - Railway
     - PythonAnywhere
     - Fly.io

3. **Custom domain**
   - Buy a domain from Namecheap, Google Domains, or Porkbun.
   - Point the domain to the static host.
   - Use HTTPS provided by the hosting platform.

## Deploy public pages on Netlify

1. Create a Netlify account and new site.
2. Connect your GitHub repository or drag-and-drop the site folder.
3. Set the publish directory to the root (`/`).
4. Use `netlify.toml` for deployment behavior.
5. After deploy, update `robots.txt` and `sitemap.xml` with your actual domain.

## Deploy the Python backend on Render

1. Create a Render account and new web service.
2. Connect your GitHub repository.
3. Use `render.yaml` and `requirements.txt` from the repo.
4. Set the start command to:
   ```bash
   python3 server.py
   ```
5. Render will provide a public HTTPS URL for the backend.

## Connect the frontend to the backend

1. In your public site, use the Render service URL as the backend domain.
2. If the frontend and backend are on different domains, make sure your backend allows CORS.

## Optional GitHub setup

1. Initialize a Git repo in the project root:
   ```bash
   git init
   git add .
   git commit -m "Initial deployment setup"
   ```
2. Push to GitHub:
   ```bash
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```

## Important SEO notes

- Do not publish `admin.html` and `admin-login.html` publicly.
- Keep the `robots.txt` entries for admin pages.
- Update `sitemap.xml` with the real website domain.
- Submit the sitemap to Google Search Console.
