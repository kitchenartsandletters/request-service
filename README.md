Request-Service

This project enables customers to express interest in out-of-stock products, and gives admins a dashboard to view those interest requests.

⸻

✅ Project Overview

This full-stack system consists of:
	•	Frontend: Vite + React + TypeScript
	•	Backend: FastAPI
	•	Database: Supabase (PostgreSQL)
	•	Hosting: Railway (both frontend and backend)

⸻

🔧 Key Functionality

Users
	•	Submit interest in out-of-stock products (email, product ID, product title)

Admins
	•	View the 100 most recent interest submissions in a secure dashboard at admin.kitchenartsandletters.com

⸻

⚙️ Environment Variables

Frontend (.env)

VITE_API_BASE_URL=https://outofstock-notify-production.up.railway.app
VITE_ADMIN_TOKEN=devtesttoken123

Backend (Railway ENV)

VITE_ADMIN_TOKEN=devtesttoken123


⸻

🔁 API Endpoint Summary

POST /api/interest

Submits an interest request.
Request body:

{
  "email": "user@example.com",
  "product_id": 123,
  "product_title": "Example Title"
}

GET /api/interest?token=YOUR_ADMIN_TOKEN

Returns a list of recent interest submissions.
Protected by token: must match VITE_ADMIN_TOKEN.

- POST /api/blacklist/export_snippet — Uploads Liquid snippet to Shopify theme with blacklisted product IDs and barcodes.

⸻

⚠️ Key Debugging Fixes
	•	✅ VITE_API_BASE_URL must be fully qualified (e.g. https://...)
	•	✅ Removed extraneous = in fetch:

`${VITE_API_BASE_URL}/api/interest?token${VITE_ADMIN_TOKEN}` // ✅ no '='


	•	✅ FastAPI now includes CORS middleware to allow frontend-to-backend requests.
	•	✅ All backend routes are mounted under /api prefix (/api/interest).
	•	✅ Backend responds with JSON { success: true, data: [...] }, which is handled in the React frontend.
	•	✅ Blacklist system fully refactored to use `product_id` as primary key, with `barcode` as optional secondary.
	•	✅ Backend upsert logic skips null/empty barcodes to prevent DB constraint violations.
	•	✅ Supabase `blacklisted_barcodes` table updated: removed `barcode` uniqueness constraint; composite uniqueness enforced via logic.
	•	✅ Export logic now generates Liquid snippet for both `product_ids` and `barcodes` and injects directly into `main-product.liquid`.

⸻

🚀 Deployment Instructions

1. Frontend Deployment (Railway)

Initial Setup
	•	Connect Railway frontend project to your GitHub repo
	•	In Settings > Environment, add:

VITE_API_BASE_URL=https://outofstock-notify-production.up.railway.app
VITE_ADMIN_TOKEN=your_admin_token_here



Build & Publish
	•	Railway auto-builds from the root of the frontend folder
	•	Make sure vite.config.ts is properly configured for production builds
	•	On successful deploy, Railway assigns a production URL (e.g. https://admin.kitchenartsandletters.com)

⸻

2. Backend Deployment (Railway)

Initial Setup
	•	Connect backend folder as a separate service in Railway
	•	Entry point must be app.main:app (FastAPI)
	•	Add this to Settings > Environment:

VITE_ADMIN_TOKEN=your_admin_token_here



Enable CORS (in main.py)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Deploy
	•	On git push, Railway will auto-build and restart the backend container
	•	The backend will be available at a subdomain like:
https://outofstock-notify-production.up.railway.app

⸻

**Snippet Export Integration (Shopify Theme Update)**
- `POST /api/blacklist/export_snippet?token=...` generates and injects updated Liquid snippet into the live Shopify theme.
- Updates both `snippets/blacklisted-barcodes.liquid` and `sections/main-product.liquid` to control visibility of the Request Form.
- Product page behavior is now controlled via:
  ```
  {% assign blacklisted_product_ids = "..." | split: "," %}
  {% assign blacklisted_barcodes = "..." | split: "," %}
  ```

⸻

3. Local Development

Backend (FastAPI)

cd backend
uvicorn app.main:app --reload

Frontend (Vite)

cd frontend
npm run dev

Make sure .env contains the correct local VITE_API_BASE_URL, e.g.:

VITE_API_BASE_URL=http://localhost:8000


⸻

🧩 Next Steps

✅ Recently Completed
- Added Shopify frontend **customer name** field alongside email; payload now includes `customer_name`.
- Backend updated to accept and store `customer_name`; UI shows a **Customer** column with sorting/search support.
- Implemented **Status** column with 6-phase dropdown; sorts by phase order (not alphabetically) and re-sorts optimistically on change.
- Atomic status updates via Supabase RPC `update_status_with_log`; de-duped logging; added debug logging in routes and client.
- Enriched inserts with Shopify **collection handles/titles** and **tags**; implemented **Out-of-Print** vs **Frontlist** backend filter.
- `GET /api/interest` now supports `collection_filter`, pagination (`page`, `limit`); frontend dropdown added for collection filter.
- Backfill scripts for tags/collections/handles improved with **retry + rate limiting** mitigation and handling of **null/empty arrays**.
- Implemented **pagination** (`page`, `limit`) in backend + UI; page summary (`X–Y of Z`) now displays; dropdown filter integrates with pagination.
- Added a **pagination selector** (20/50/100) and persist selected page size + collection filter via localStorage.
- Advanced filtering: OOP definition in sync (tags `op`/`pastop`, OOP collections, or title starting with "OP: ").
- Statuses changed to New → In Progress → Request Filed → Complete
- Added full-featured **Blacklist Manager**:
  - Allows admin to search Shopify for a product by barcode or ID, preview results, and add to a server-side blacklist table.
  - Exporting the blacklist generates a Liquid snippet used by the Online Store to conditionally suppress the request form on select product pages.
  - Snippet injection now writes directly to the live theme's `main-product.liquid`, replacing or inserting the assignment logic.
- Added **RightSidebar** component with support for dual-mode display (row-based details or Markdown doc viewer). Replaced ConfirmModal-based doc display with a persistent sidebar. Markdown viewer now supports image styling, GFM formatting (bullets, lists), and relative image paths using `@tailwindcss/typography`.
- Improved RightSidebar: support click-outside and "Close" button to trigger slide-out animation.
- Fixed search and filter so they now apply across the entire dataset, not just the current page.
- Backend `/api/interest` updated with server-side filtering and pagination aware of filters.
- Frontend now wires filters and search directly into backend fetch; local-only filtering removed.
- Page reset on filter change now ensures dataset view is correct (always snaps to valid page).
- 🧪 Add tests for export snippet functionality and error handling (invalid token, missing theme, malformed data).

📌 Next Steps
- UI polish: scale down table font size, explore per-option color cues for the status dropdown.
- Consider full per-option colorization using a custom Listbox component (only if users request it).
- Extend logging to track admin interactions by specific user for auditing (replace hard-coded "admin" - add users).
- Handle **page reset on filter change** (snap to last valid page if current page exceeds dataset).
- Row actions: add **archive** / **delete** functionality.
- Add a **request history log** in the dashboard (status change trail).
- Modals for manual **create/edit**; support **bulk editing** abilities.
- Notifications: Slack/email on new submissions and/or status changes.
- Validation: tighten whitespace-only name handling in Shopify UI and optionally enforce server-side sanitization.
- Data retention & privacy: implement automatic archiving/deletion (e.g., delete open requests after 12 months; archive after fulfillment) and update Privacy Policy accordingly.
- Extract title dynamically from Markdown file and display in sidebar header.

⸻

Blacklist Manager Guide

The Blacklist Manager allows staff to suppress the "Request Form" on product pages of items that are no longer relevant for restock. This is especially useful for permanently discontinued titles, one-time sets, or ephemeral imports.

HOW IT WORKS
- Barcodes and Product IDs are matched against Shopify's live catalog.
- If a match is found, it is added to the blacklist table.
- Clicking "Export to Shopify" rewrites the blacklisted barcodes in the live theme.
- That snippet is referenced on product pages to determine whether to show or hide the Request Form.
- The logic is inserted directly into the live theme

STEP-BY-STEP USAGE

1. Navigate to the Blacklist tab in the Admin Dashboard. It is located within the Request Service menu item.
![Tap UI](/docs-screenshots/blacklist-manager/tab-ui.gif)

2. In the input box, enter a barcode or Shopify Product ID to search (the entry field will accept either).
![Input Box](/docs-screenshots/blacklist-manager/input-box.gif)

3. Preview product details returned by Shopify in a modal before confirming.
   - Product Title
   - Author (SKU field)
   - Handle
   - Product ID
   - Barcode

4. Click “Confirm All” to save the entries to the database after previewing the products.
![Preview Modal](/docs-screenshots/blacklist-manager/preview-modal.gif)

5. Once your list is built, click “Export to Shopify”.
![Export to Shopify](/docs-screenshots/blacklist-manager/export-shopify.gif)
   - This will:
     - Update blacklisted barcodes in the live theme.

6. You should now see the request form hidden on blacklisted product pages.

BULK ADDING

If you have multiple barcodes or product IDs to add:
- You can paste multiple barcodes or product IDs separated by commas, spaces, or newlines.
- The system will iterate through them and attempt to add each.
- If a barcode is invalid or does not resolve to a product, it will be skipped.

⚠️ Reminder: “Export to Shopify” must be clicked to publish changes to Shopify. This applies to adding or removing entries.

⸻

🛠️ Incident Summary: Product ID Refactor, Timeouts, and Resolution

On September 18, 2025, a series of refactors were implemented to correct brittle behavior in the blacklist export system. Key discoveries and fixes:

- The initial blacklist implementation used `barcode` as the unique identifier, which caused issues for products with missing or empty barcodes (e.g., custom prints or used books).
- Supabase began rejecting entries due to NOT NULL constraints when barcodes were absent.
- We refactored all logic to prioritize `product_id` as the primary key for blacklist enforcement. Barcodes remain useful as a fallback.
- Shopify export logic was updated to generate a Liquid snippet with both product IDs and barcodes and to inject it directly into the live `main-product.liquid` template.
- A sudden surge of 408, 499, and 401 errors led to a discovery that proxy authentication was being incorrectly applied to all routes.
- We updated `server.js` to apply Basic Auth **only to static frontend content**, while leaving backend `/api` routes publicly accessible.
- DNS issues were ruled out after confirming correct record resolution.
- Stability returned after rollback to a stable commit, manual patch restoration, and re-deploy. The Admin Dashboard is now functioning reliably.