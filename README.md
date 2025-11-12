# Project AEGIS - Anticipatory Engine for Geolocated Intervention against Scams

**SIH 2025 Finals | Transforming Cybercrime Response from Reactive to Anticipatory**

## Overview

Project AEGIS is a full-stack MVP that enables citizens to file anonymized scam complaints and provides law enforcement with real-time, predictive intelligence to interdict cash withdrawals at high-risk locations within 90 minutes.

## 🎯 Core Features

### Citizen Portal (`/citizen`)
- **Anonymized Complaint Submission**: File scam reports with zero PII storage
- **Smart Location Detection**: Auto-detect location or pin on interactive map
- **Multiple Scam Types**: Support for UPI phishing, fake loan apps, impersonation, etc.
- **Instant Feedback**: Real-time confirmation with reference ID

### LEA Dashboard (`/lea`)
- **Real-time Intelligence**: Live map showing complaints and predicted hotspots
- **AI-Powered Predictions**: Rule-based engine identifying high-risk cash-out locations
- **Digital Cordon System**: Geofenced areas with simulated NPCI integration
- **Feedback Loop**: Track prediction accuracy and system learning

### Backend System
- **FastAPI REST API**: High-performance Python backend
- **PostgreSQL + PostGIS**: Spatial database for location intelligence
- **Rule-Based AI Engine**: Confidence-scoring prediction system
- **Mock Alert Service**: Simulated Twilio SMS and SendGrid email alerts

## 🏗️ Architecture

```
Frontend (Next.js 16 + React 19)
├── Citizen Portal - Complaint submission
├── LEA Dashboard - Real-time intelligence
└── Navigation & Layout

Backend (FastAPI + Python)
├── Complaint Management API
├── AI Prediction Engine
├── Alert Service (Mock)
└── Digital Cordon System

Database (PostgreSQL + PostGIS)
├── Complaints (anonymized)
├── High-risk ATMs (pre-seeded)
├── Hotspot predictions
├── Digital cordons
└── System metrics
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- PostgreSQL with PostGIS extension
- Supabase account (for cloud database)

### Frontend Setup

```bash
# Install dependencies
npm install

# Configure environment variables
cp .env.local.example .env.local
# Edit .env.local with your configuration

# Run development server
npm run dev
```

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your database credentials

# Run development server
uvicorn main:app --reload
```

### Database Setup

```bash
# Run schema creation
psql -d your_database -f database/schema.sql

# Seed high-risk ATM data
psql -d your_database -f database/seed_atms.sql
```

## 📊 How It Works

### 1. Complaint Submission
- Citizen files anonymous complaint with scam type, amount, and location
- System validates input and stores in PostgreSQL database
- Zero PII stored - only coordinates and transaction details

### 2. AI Prediction Engine
- **Rule-based algorithms** analyze complaint patterns
- **Confidence scoring** (0-100%) for each prediction
- **Top 3 locations** identified within specified radius

#### Prediction Rules:
- **Fake Loan Apps** → Highway/Bus Stand ATMs (85% confidence)
- **UPI Phishing** → Railway Station ATMs (85% confidence)
- **Amount > ₹50,000** → ATMs within 2km of victim (90% confidence)
- **Default Rule** → City Center ATMs (75% confidence)

### 3. Real-time Intelligence
- **LEA Dashboard** updates every 30 seconds
- **Hotspot visualization** with pulsing indicators
- **Countdown timers** showing prediction validity (90 minutes)
- **Interactive controls** for LEA action

### 4. Digital Cordon System
- **2km radius** geofenced area around hotspot
- **45-minute duration** with automatic expiry
- **NPCI simulation** for transaction monitoring
- **Visual indicators** on LEA dashboard

### 5. Alert System
- **High-confidence predictions** (>80%) trigger alerts
- **Mock SMS alerts** via Twilio simulation
- **Mock email alerts** via SendGrid simulation
- **Audit trail** for compliance and monitoring

## 🔒 Privacy & Compliance

- **Zero PII Storage**: No names, phone numbers, or personal data
- **DPDP Act 2023 Compliant**: Data minimization and purpose limitation
- **Anonymized Locations**: Only coordinates stored, no exact addresses
- **Row Level Security**: Database access controls and audit trails

## 📈 System Metrics

- **Complaint Processing**: < 2 seconds
- **Dashboard Load Time**: < 3 seconds
- **Prediction Latency**: < 1 second
- **System Accuracy**: 58% (simulated for MVP)
- **PII Stored**: 0 bytes

## 🧪 Testing Scenarios

### Test Case 1: High-Value Fake Loan App
1. Navigate to `/citizen`
2. Select "Fake Loan App" as scam type
3. Enter amount: ₹75,000
4. Use auto-detect location
5. Submit complaint
6. Check `/lea` for hotspot prediction within 30 seconds

### Test Case 2: Digital Cordon Activation
1. On LEA dashboard, click active hotspot
2. Click "Activate Digital Cordon"
3. Verify yellow ring appears on map
4. Check 45-minute countdown timer
5. Confirm NPCI simulation in backend logs

### Test Case 3: Feedback Loop
1. Mark hotspot as "Interdicted"
2. Submit another complaint
3. Mark second hotspot as "False Alarm"
4. Check system accuracy update in metrics

## 🌟 MVP Demonstration Features

- **Complete User Journey**: End-to-end complaint to interdiction flow
- **Real-time Updates**: Live polling and dynamic dashboard
- **Interactive Controls**: Click-to-action hotspot management
- **Mock Integrations**: Simulated external services (Twilio, SendGrid, NPCI)
- **Responsive Design**: Mobile-friendly interface
- **Performance Metrics**: Sub-2-second processing times

## 📁 Project Structure

```
AEGIS/
├── src/app/                    # Next.js App Router
│   ├── citizen/               # Complaint portal
│   ├── lea/                   # LEA dashboard
│   ├── layout.tsx             # Navigation and layout
│   └── page.tsx               # Landing page
├── src/lib/                   # API client and utilities
├── src/types/                 # TypeScript definitions
├── backend/                   # FastAPI application
│   ├── app/api/              # API endpoints
│   ├── app/services/         # Business logic
│   └── main.py               # Application entry
├── database/                  # SQL schema and seed data
├── .env.local                 # Frontend environment
├── backend/.env              # Backend environment
└── README.md                 # This file
```

## 🔧 Configuration

### Frontend Environment Variables
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_DEFAULT_LAT=28.6139
NEXT_PUBLIC_DEFAULT_LON=77.2090
```

### Backend Environment Variables
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/aegis
ALERT_CONFIDENCE_THRESHOLD=0.8
PREDICTION_TIME_WINDOW_MINUTES=90
CORDON_RADIUS_METERS=2000
```

## 🚀 Deployment

### Frontend (Vercel)
```bash
npm run build
vercel --prod
```

### Backend (Render)
```bash
# Configure render.yaml
# Deploy via GitHub integration
```

### Database (Supabase)
```sql
-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Run schema and seed scripts
```

## 🤝 Contributing

This is an MVP prototype for SIH 2025 Finals. The system demonstrates:
- React 19 + Next.js 16 frontend capabilities
- FastAPI backend performance
- PostgreSQL + PostGIS spatial queries
- Real-time data visualization
- Privacy-first design principles

## 📄 License

MIT License - Built for SIH 2025 Finals demonstration purposes.

---

**Project AEGIS** - Transforming cybercrime response from reactive reporting to anticipatory disruption.