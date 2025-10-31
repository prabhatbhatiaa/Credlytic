# Credlytic

**NFT-Based Academic Record Verification**

Credlytic is a decentralized certificate issuance and verification platform built on the Aptos blockchain. The system enables educational institutions to mint tamper-proof NFT certificates and allows students to verify and retrieve their credentials on-chain.

---

## 🎯 Features

- **NFT Certificate Minting**: Issue blockchain-verified academic certificates as non-fungible tokens
- **Student Verification**: Query and retrieve certificates using wallet addresses
- **Automated Certificate Generation**: Dynamic PNG certificate creation with personalized student data
- **Blockchain Integration**: Full Aptos DevNet integration with transaction tracking
- **RESTful API**: Clean endpoints for certificate operations
- **Multiple Indexer Fallbacks**: Robust querying with automatic failover across Aptos indexer endpoints

---

## 🏗️ Architecture

```
credlytic-fin/
├── backend/
│   ├── app.py                 # Flask API server with minting & verification endpoints
│   ├── create_collec.py       # Collection initialization script (one-time setup)
│   └── generated/             # Certificate PNG storage
│
└── frontend/
    ├── index.html             # Web interface
    ├── app.js                 # Frontend logic
    └── style.css              # Styling
```

### Tech Stack

**Backend**
- Python 3.11
- Flask + Flask-CORS
- Aptos Python SDK
- Pillow (image generation)
- python-dotenv

**Blockchain**
- Aptos DevNet
- Token Standard v3
- GraphQL Indexer API

**Frontend**
- Vanilla JavaScript
- HTML5/CSS3

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Aptos wallet with DevNet APT tokens
- Private key for the issuing institution

### Installation

1. **Clone the repository**
   ```powershell
   git clone <repository-url>
   cd credlytic
   ```

2. **Install Python dependencies**
   ```powershell
   pip install flask flask-cors requests python-dotenv pillow aptos-sdk urllib3
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   UNIVERSITY_PRIVATE_KEY=0x<your_private_key_here>
   ```

4. **Initialize the NFT collection** (one-time setup)
   ```powershell
   python backend\create_collec.py
   ```

5. **Start the backend server**
   ```powershell
   python backend\app.py
   ```
   
   Server will start at `http://127.0.0.1:5000`

6. **Launch the frontend**
   
   Open `frontend/index.html` in your browser or serve via HTTP server.

---

## 📡 API Reference

### Create Certificate
```http
POST /create-cert
Content-Type: application/json

{
  "name": "Student Name",
  "course": "Course Name",
  "student_id": "0x<aptos_wallet_address>"
}
```

**Response**
```json
{
  "success": true,
  "tx_hash": "0x...",
  "explorer_url": "https://explorer.aptoslabs.com/txn/...",
  "download_url": "http://127.0.0.1:5000/download/Certificate_...",
  "message": "Certificate minted successfully!"
}
```

### Retrieve Student Certificates
```http
POST /get-my-certs
Content-Type: application/json

{
  "student_id": "0x<aptos_wallet_address>"
}
```

**Response**
```json
{
  "certificates": [
    {
      "name": "Certificate: Student Name #1730419200",
      "explorer_url": "https://explorer.aptoslabs.com/txn/...",
      "download_url": "http://127.0.0.1:5000/download/..."
    }
  ]
}
```

---

## ⚠️ Current Status

**Work in Progress** — Core functionality is operational but some features are incomplete.

Development has been impacted by ongoing **Aptos API infrastructure issues**, including:
- Indexer endpoint instability
- Rate limiting inconsistencies  
- DNS resolution failures on certain endpoints

These are external dependencies beyond our control. The codebase includes multiple fallback mechanisms to mitigate these issues, but full feature completion is pending API stabilization from Aptos.

---

## 🛠️ Troubleshooting

**Backend fails to start**
- Verify `UNIVERSITY_PRIVATE_KEY` is set correctly in `.env`
- Ensure all dependencies are installed
- Check Python version (requires 3.11+)

**Certificate query returns empty**
- Aptos indexer may be experiencing downtime
- Try again after a few minutes (automatic fallback is built-in)
- Verify wallet address format starts with `0x`

**Frontend can't connect**
- Confirm backend is running on port 5000
- Check browser console for CORS errors
- Ensure you're accessing frontend via same origin or CORS is configured

---

## 🤝 Contributing

Contributions are welcome. Please open an issue to discuss proposed changes before submitting a pull request.

---

**Note**: This project uses Aptos DevNet for testing. Tokens and transactions have no real-world value.
