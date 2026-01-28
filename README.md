# Credlytic

> Web3-based certificate issuance and verification system on Aptos Devnet

A lightweight, production-ready system for issuing blockchain-verified digital certificates. Admins mint certificates as NFTs on Aptos, students receive beautifully designed PDFs via email, and employers verify authenticity on-chain in seconds.

## ✨ Features

- **Blockchain Minting** — Issues certificates as NFTs on Aptos Devnet with permanent on-chain records
- **Google OAuth Admin Login** — Secure admin authentication with wallet binding (Petra)
- **Automated Email Delivery** — Sends certificate PDFs with transaction links automatically
- **Beautiful Certificate Design** — Custom template-based generation with Inter font
- **Instant Verification** — Employers verify certificates using email + transaction hash
- **Multi-Role Interface** — Separate portals for Admin, Student, and Employer
- **Dark/Light Theme** — Clean UI with persistent theme toggle

## 🏗️ Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Admin     │────-───▶│    Flask     │─────-──▶│   Aptos     │
│  (Google +  │         │   Backend    │         │   Devnet    │
│   Petra)    │         │              │         └─────────────┘
└─────────────┘         └──────────────┘                 │
                               │                         │
                               │ Mints NFT               │
                               ▼                         │
                        ┌──────────────┐                 │
                        │   Generate   │                 │
                        │  Certificate │                 │
                        │   PDF/PNG    │                 │
                        └──────────────┘                 │
                               │                         │
                               ▼                         │
                        ┌──────────────┐                 │
                        │  Email via   │                 │
                        │  SMTP/Gmail  │                 │
                        └──────────────┘                 │
                               │                         │
                               ▼                         │
                        ┌──────────────┐                 │
                        │   Student    │                 │
                        │   Receives   │                 │
                        │   PDF        │                 │
                        └──────────────┘                 │
                                                         │
┌─────────────┐         ┌──────────────┐                 │
│  Employer   │──────-─▶│   Verify     │─────────────────┘
│             │         │  Endpoint    │  Checks on-chain
└─────────────┘         └──────────────┘
```

## 📁 Project Structure

```
credlytic-aarambh/
├── backend/
│   ├── app.py                 # Flask API (routes, auth, issuance)
│   ├── admin_mint.py          # Aptos NFT minting + certificate generation
│   ├── create_collec.py       # Collection creation on Aptos
│   ├── email_utils.py         # Email sending with attachments
│   ├── template.png           # Certificate base template
│   ├── admin.json             # Admin wallet bindings (auto-generated)
│   ├── db.json                # Certificate records (auto-generated)
│   └── generated/             # Generated certificate PDFs
│
├── frontend/
│   ├── index.html             # Landing page with 3 portals
│   ├── admin.html             # Admin certificate issuance UI
│   ├── dashboard.html         # Admin dashboard view
│   ├── employer.html          # Employer verification interface
│   ├── student.html           # Student certificate lookup
│   ├── style.css              # Global styles + theme system
│   ├── theme.js               # Theme persistence logic
│   └── fonts/
│       └── inter.ttf          # Inter font for certificates
│
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Gmail account with App Password (for email delivery)
- Aptos Devnet wallet (for admin minting)

### 1. Clone & Setup

```powershell
# Clone the repository
git clone https://github.com/prabhatbhatiaa/credlytic.git
cd credlytic

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install flask flask-cors pillow python-dotenv aptos-sdk
```

### 2. Environment Configuration

Create a `.env` file in the `backend/` directory:

```env
# Aptos Wallet (Admin/University)
UNIVERSITY_PRIVATE_KEY=0xyourprivatekeyhere

# Email Configuration (Gmail App Password recommended)
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password-here
```

**Security Note:** Never commit `.env` to git. It's already in `.gitignore`.

### 3. Run the Application

```powershell
cd backend
python app.py
```

Server starts at `http://localhost:5000`

### 4. Access the System

- **Landing Page:** http://localhost:5000
- **Admin Portal:** http://localhost:5000/admin
- **Student Portal:** http://localhost:5000/student
- **Employer Verification:** http://localhost:5000/employer

## 🔐 Admin Setup Flow

1. **Google Sign-In** — Admin logs in with authorized Google account
2. **Wallet Binding** — Connect Petra wallet (one-time, stored in `admin.json`)
3. **Issue Certificates** — Fill student details, mint NFT, generate PDF, send email
4. **Dashboard** — View all issued certificates

## 📋 API Endpoints

### Admin Authentication
- `POST /api/admin/login_check` — Verify Google admin email
- `POST /api/admin/bind_start` — Initiate wallet binding
- `POST /api/admin/bind_finish` — Complete wallet binding with signature

### Certificate Management
- `POST /api/admin/issue` — Issue new certificate (mint + email)
- `GET /api/student/certificates?email=` — Retrieve student's certificates
- `POST /api/employer/verify` — Verify certificate by email + tx hash
- `GET /generated/<filename>` — Serve certificate files

## 🎨 Certificate Generation Flow

1. Load `template.png` base design
2. Overlay student name, course, date using Inter font
3. Add transaction hash and Aptos explorer link
4. Generate both PNG and PDF versions
5. Store in `backend/generated/` with timestamped filename
6. Send via email with attachment

## 🔍 Employer Verification

Employers verify certificates by providing:
- **Student Email** — Recipient's email address
- **Transaction Hash** — Blockchain transaction ID (from certificate or email)

The system checks:
1. Certificate exists in database for that email
2. Transaction hash matches stored record
3. Returns certificate details + Aptos explorer link

## 🛠️ Technology Stack

**Backend:**
- Flask (Python web framework)
- Aptos SDK (blockchain interaction)
- Pillow (image/PDF generation)
- SMTP (email delivery)

**Frontend:**
- Vanilla HTML/CSS/JavaScript
- Google OAuth (admin authentication)
- Petra Wallet SDK (Aptos wallet integration)

**Blockchain:**
- Aptos Devnet (NFT minting)
- Custom Move contracts for certificate collection

## 📦 Dependencies

```txt
flask>=2.3.0
flask-cors>=4.0.0
pillow>=10.0.0
python-dotenv>=1.0.0
aptos-sdk>=0.6.0
```

Create `backend/requirements.txt` with the above and run:
```powershell
pip install -r backend/requirements.txt
```

## 🚢 Deployment Options

### Frontend (Static)
- **GitHub Pages** — Free, HTTPS, custom domain support
- **Netlify** — Auto-deploy from git with form handling
- **Cloudflare Pages** — Fast global CDN

### Backend (Flask API)
- **Fly.io** — Containers with free tier, easy deployment
- **Deta Micros** — Serverless Python, generous free tier
- **Railway** — Simple git-based deployments

**Multi-host High Availability:**
Deploy backend to 2+ free hosts, use Cloudflare Workers as failover proxy.

## 🔒 Security Considerations

- Admin emails are whitelisted in `ALLOWED_ADMIN_EMAILS`
- Wallet binding uses cryptographic signature verification
- Environment variables for all secrets
- CORS configured for Google OAuth compatibility
- Transaction hashes normalized for matching (case-insensitive)

## 📝 Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `UNIVERSITY_PRIVATE_KEY` | Aptos wallet private key (hex) | `0x123abc...` |
| `EMAIL_ADDRESS` | Sender email address | `admin@example.com` |
| `EMAIL_PASSWORD` | Email app password (not account password) | `abcd efgh ijkl mnop` |

## 🐛 Troubleshooting

**Email not sending:**
- Check Gmail App Password is set correctly
- Enable "Less secure app access" if using standard Gmail
- Verify firewall allows SMTP port 587/465

**Aptos transaction fails:**
- Ensure wallet has testnet APT (get from faucet)
- Check `UNIVERSITY_PRIVATE_KEY` format (must include `0x` prefix)
- Verify Devnet is operational: https://status.aptoslabs.com

**Certificate not generating:**
- Confirm `template.png` exists in `backend/`
- Check `frontend/fonts/inter.ttf` is present
- Verify Pillow library is installed

## 🎯 Roadmap

- [ ] Replace `db.json` with PostgreSQL/SQLite
- [ ] Add QR codes with verify URLs to certificates
- [ ] Bulk certificate issuance (CSV import)
- [ ] Admin dashboard analytics
- [ ] Certificate revocation system
- [ ] Multi-language support
- [ ] Mobile-responsive UI improvements
- [ ] Mainnet deployment guide

## 👤 Author

**Prabhat Bhatia**

---

**Note:** This system uses Aptos Devnet. For production, migrate to Mainnet and implement additional security measures (rate limiting, DDoS protection, formal audits).

