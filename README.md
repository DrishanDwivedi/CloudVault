# ☁️ CloudVault — Intelligent Multi-Tier Cloud Storage Platform

> **Automated, Policy-Driven Data Lifecycle Orchestration Across Heterogeneous Storage Tiers (Hot, Warm, Archive)**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/Frontend-React_18_(Vite)-61DAFB.svg)](https://react.dev/)
[![Storage](https://img.shields.io/badge/Storage-MinIO_|_SeaweedFS_|_Garage_S3-FF6B6B.svg)]()
[![Security](https://img.shields.io/badge/Security-OAuth2_|_JWT_|_Bcrypt_|_SHA--256-green.svg)]()

---

## 📌 Executive Summary

Enterprise data volume expands exponentially, yet industry telemetry reveals that **over 80% of stored unstructured data becomes dormant within 30 to 90 days** after creation. Keeping inactive "cold" data on expensive primary tier storage (NVMe/SSD arrays or AWS S3 Standard) inflates infrastructure budgets by up to 70%.

**CloudVault** is a vendor-agnostic, self-hosted multi-tier cloud storage platform that automatically orchestrates data lifecycle migration across **Hot (MinIO)**, **Warm (SeaweedFS)**, and **Archive (Garage S3)** tiers based on granular, customizable time policies—guaranteeing **zero data loss** through cryptographic **SHA-256 checksum verification**.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        React 18 + Vite Frontend                        │
│   • File Explorer     • Lifecycle Console     • Live Recent Actions    │
│   • Storage Analytics • Health Indicator      • Real-Time Polling (2.5s)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST (OAuth2 Bearer JWT)
┌───────────────────────────────────▼────────────────────────────────────┐
│                        FastAPI Asynchronous Backend                    │
│   ┌────────────────────┬───────────────────────┬───────────────────┐   │
│   │ Auth & Security    │ File & Folder Service │ Policy Sweeper    │   │
│   │ (JWT/Bcrypt/RBAC)  │ (CRUD + Atomic Locks) │ (3s Daemon Loop)  │   │
│   └────────────────────┴───────────────────────┴───────────────────┘   │
│                                   │                                    │
│                     Unified Storage Adapter Interface                  │
│                     (BaseStorageAdapter Abstraction)                   │
└─────────┬─────────────────────────┼─────────────────────────┬──────────┘
          │                         │                         │
          ▼                         ▼                         ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│     HOT TIER     │      │    WARM TIER     │      │   ARCHIVE TIER   │
│    MinIO (S3)    │      │    SeaweedFS     │      │    Garage S3     │
│   Port: 9000     │      │   Port: 8333     │      │   Port: 3900     │
│ High-IOPS Active │      │ Append-Only Read │      │ Resilient Cold   │
└──────────────────┘      └──────────────────┘      └──────────────────┘
```

---

## 🚀 Storage Tier Breakdown

| Tier | Engine | Port | Hardware Profile | Purpose & Real-World Analogy |
| :--- | :--- | :--- | :--- | :--- |
| **Hot** | **MinIO S3** | `9000` | NVMe / Enterprise SSD | High IOPS, ultra-low latency for active, frequently edited files (equivalent to **AWS S3 Standard**). |
| **Warm** | **SeaweedFS** | `8333` | High-capacity HDD arrays | High throughput, append-only volume store optimized for small & medium files (equivalent to **AWS S3 Infrequent Access**). |
| **Archive** | **Garage S3** | `3900` | Dense JBOD / Cold Nodes | Geo-distributed, lightweight, low-power archival storage (equivalent to **AWS S3 Glacier / Deep Archive**). |

---

## 🛡️ Security, Authentication & Data Integrity

### 1. Stateless Authentication (OAuth2 + JWT + Bcrypt)
- **Password Protection**: Passwords are never stored in plaintext. They are salted and hashed using **Bcrypt** (`bcrypt.gensalt()`).
- **Token Format**: Standard OAuth2 Password Bearer flow issuing **HS256 signed JSON Web Tokens (JWT)** with strict expiration timestamps (`exp`).
- **Authorization**: Endpoints use FastAPI dependency injection (`Depends(get_current_user)`) to validate credentials on every request.

### 2. Role-Based Access Control (RBAC)
- **Standard Users**: Can upload, download, organize, and delete their own files (`owner_id` tenancy isolation).
- **Administrators**: Can adjust policy durations, trigger sweeps, inspect server health, and view system-wide audit activity logs.

### 3. Non-Destructive Two-Phase Migration & Integrity
- **SHA-256 Checksumming**: Computed during file upload and stored in metadata. During migration, the destination engine re-computes the SHA-256 hash upon writing. The source object is **purged only after the hash is validated**.
- **Atomic Concurrency Locks**: While in transit, a file's state transitions to `migrating`, preventing race conditions from concurrent downloads or deletes.
- **Failover & Recovery**: Built-in `recover_stalled_migrations()` detects interrupted transfers after unexpected server crashes and safely reverts files back to `active`.

---

## 👥 4-Member Group Role Division (For Viva Defense)

| Team Member | Role | Primary Presentation Focus |
| :--- | :--- | :--- |
| **Member 1 (Backend Lead)** | Backend & Storage Specialist | FastAPI REST architecture, Storage Adapters (MinIO, SeaweedFS, Garage), Automated Migration Daemon, Concurrency & SHA-256 integrity. |
| **Member 2** | Frontend & UI/UX Engineer | React 18 / Vite dashboard, 2.5s real-time state polling, dynamic tier badges, policy sliders, and live audit feed. |
| **Member 3** | System Architect & Research Lead | Problem identification (the 80/20 data dormancy rule), objectives, literature review (AWS S3 Intelligent-Tiering, Ceph), and research gap. |
| **Member 4** | DevOps, Security & Impact Analyst | JWT authentication, RBAC, cost reduction modeling (up to 70% savings), green computing / carbon footprint reduction, and feasibility. |

---

## 📋 Evaluation Card Parameters & Viva Script

### Parameter 1: Problem Identification & Objectives
- **Problem**: 80% of enterprise data is cold within 90 days. Storing cold data on NVMe / AWS S3 Standard costs up to $0.023/GB/mo, wasting huge budgets with vendor lock-in.
- **Objectives**: Build an on-premise, vendor-neutral multi-tier platform with automated background migration and SHA-256 cryptographic verification.

### Parameter 2: Literature Review & Research Gap
- **Literature**: AWS S3 Intelligent-Tiering charges monthly monitoring fees per 1,000 objects with 128 KB minimum object sizes. Ceph is robust but notoriously heavy and complex to administer.
- **Research Gap**: Lack of lightweight, plug-and-play heterogeneous storage orchestrators providing second/minute-level granular scheduling for live auditing and testing.

### Parameter 3: Project Methodology
- **Ingestion**: Multipart upload &rarr; SHA-256 hash computed &rarr; stored in MinIO Hot &rarr; metadata cataloged in database with `next_migration_date = NOW() + duration`.
- **Migration Pipeline**: Background daemon identifies qualifying objects &rarr; acquires atomic database lock (`status = 'migrating'`) &rarr; streams from source to destination &rarr; validates destination checksum &rarr; purges source &rarr; updates metadata & writes to audit log.

### Parameter 4: Implementation, Outcomes & Live Demo
1. Open `http://localhost:5173` & log in (`admin@example.com` / `Admin@123`).
2. Show **Infrastructure Card**: Metadata DB, MinIO, SeaweedFS, Garage S3 all **ONLINE**.
3. Go to **Lifecycle & Storage Console &rarr; Policies Tab**:
   - Hot &rarr; Warm: set to **5 Seconds**.
   - Warm &rarr; Archive: set to **5 Seconds**.
4. Upload any document via **+ New**.
5. Watch the file row:
   - Initial state: **`HOT`** (MinIO).
   - After 5 seconds: **`WARM`** (SeaweedFS).
   - After another 5 seconds: **`ARCHIVE`** (Garage S3).
6. Show **Recent Actions**: Point out the live audit trail with timestamps and checksums.

### Parameter 5: Project Complexity
- Multi-storage adapter pattern bridging three distinct engine APIs.
- Atomic state locking and non-destructive transfer semantics preventing race conditions.
- Automated crash recovery (`recover_stalled_migrations()`).
- High-precision sub-minute floating-point scheduling (`duration_days = 5 / 86400`).

### Parameter 6: Cost, Feasibility & Societal Impacts
- **Cost**: Offloading 75% of inactive data from high-cost SSD ($0.20/GB/mo) to cold storage ($0.004/GB/mo) cuts total infrastructure costs by **60% to 75%**.
- **Green Computing**: Cold archival nodes require less cooling and allow drive spin-downs, directly cutting data center carbon emissions.
- **Data Sovereignty**: Open-source, on-premise operation protects sensitive healthcare/financial data without relying on foreign public clouds.

### Parameter 7: Teamwork & Group Dynamics
- Shared Git repository with modular boundaries: Frontend, Backend API, Storage Adapters, DevOps/Testing.
- Collaborative end-to-end integration and failover simulation testing.

---

## 🎯 Universal Core Blueprint (Mandatory for ALL 4 Members)

> **Important**: In final evaluations, the examination panel may cross-question ANY team member on ANY area. Every student in the group must master these 5 core points:

1. **30-Second Elevator Pitch**:
   *"CloudVault is an automated, vendor-neutral multi-tier cloud storage platform. It solves cloud storage budget inflation by automatically migrating aging, dormant data from high-IOPS Hot storage (MinIO) to high-throughput Warm storage (SeaweedFS) and low-power Archive storage (Garage S3) using configurable time policies—guaranteeing zero data loss with SHA-256 cryptographic checksums."*
2. **End-to-End Data Journey**:
   Upload &rarr; SHA-256 computed &rarr; saved in MinIO (Hot) &rarr; metadata stored in DB &rarr; 3-second background worker scans eligibility &rarr; file locked to `migrating` &rarr; transferred to SeaweedFS (Warm) &rarr; SHA-256 verified &rarr; source purged &rarr; after warm duration, transferred to Garage S3 (Archive) &rarr; React polls every 2.5s and updates badge live.
3. **Storage Engines & Ports**:
   - Hot: **MinIO S3** (Port 9000, NVMe equivalent)
   - Warm: **SeaweedFS** (Port 8333, HDD array equivalent)
   - Archive: **Garage S3** (Port 3900, low-power cold node equivalent)
4. **Security & Cryptography**:
   - Passwords: **Bcrypt** with unique salt per user.
   - Auth: **OAuth2 Bearer JWT** tokens (`HS256`).
   - Integrity: **SHA-256** checksum verification across all hops.
   - Concurrency: Atomic database locking (`status = 'migrating'`) prevents race conditions.
5. **Business & Financial Justification**:
   Over 80% of enterprise data is cold within 90 days. Primary storage costs ~$0.023/GB/mo, while cold archive costs ~$0.001/GB/mo. Automated tiering cuts company storage budgets by **60% to 75%**.

---

## 🔄 Cross-Examination Survival Matrix

| If You Are Asked... | Give This Exact Spoken Answer: |
| :--- | :--- |
| **Frontend dev asked about Backend migration** | *"The backend uses a background daemon worker running every 3 seconds that identifies files whose policy duration expired. It locks the row to 'migrating', transfers the file, verifies the SHA-256 hash, deletes the source copy, and our React frontend catches the new tier on its next 2.5s poll."* |
| **Backend dev asked about Business ROI & Cost** | *"Primary storage costs around $0.023/GB/month vs $0.001/GB/month for cold storage. Because 80% of data is inactive within 90 days, automated tiering offloads cold data and cuts recurring storage budgets by 60% to 75%."* |
| **Research Lead asked about Data Corruption** | *"We compute a SHA-256 hash upon upload. During transfer, the destination calculates the incoming stream's hash. Only if both hashes match byte-for-byte is the source file deleted; otherwise, the migration aborts and the original file is preserved."* |
| **Security/DevOps asked about Server Crashes** | *"Our migration is non-destructive. If power fails mid-transfer, the source copy is untouched. On reboot, `recover_stalled_migrations()` finds any files stuck in 'migrating' status and safely reverts them to 'active'."* |

---

## ⚡ Quick Start & Run Commands

### Prerequisites
- Python 3.10+
- Node.js 18+
- Windows (PowerShell / Command Prompt)

### 1. Setup Storage Engines
Run the setup script once to prepare storage binaries and data directories:
```cmd
setup_services.bat
```

### 2. Launch CloudVault
Launch all storage services, FastAPI backend, and React frontend with a single command:
```cmd
start.bat
```

### 3. Access URLs
- **Web Dashboard**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **MinIO Hot Storage**: [http://localhost:9000](http://localhost:9000)
- **SeaweedFS Warm Storage**: [http://localhost:8333](http://localhost:8333)
- **Garage S3 Archive Storage**: [http://localhost:3900](http://localhost:3900)

**Default Credentials**:
- **Email**: `admin@example.com`
- **Password**: `Admin@123`

---

## ❓ Rapid-Fire Viva Q&A

**Q1: Why did you use FastAPI instead of Flask?**  
> *"FastAPI natively supports `async/await` for asynchronous I/O and high-throughput file streaming. It also provides automatic request validation using Pydantic and automatically generates interactive Swagger documentation at `/docs`."*

**Q2: Why use three separate storage engines instead of three folders in MinIO?**  
> *"Three folders inside MinIO is merely logical separation on the same hardware. Real-world enterprise tiering requires true physical heterogeneity: Hot storage runs on high-IOPS NVMe drives, Warm storage on distributed append-only volumes (SeaweedFS), and Archive on low-power cold storage nodes (Garage S3)."*

**Q3: What happens if power fails mid-migration?**  
> *"Our migration is non-destructive. The source file is never deleted until the destination payload is verified via SHA-256. Upon restart, `recover_stalled_migrations()` detects files stuck in the 'migrating' state and reverts them safely to 'active'."*

**Q4: How does the frontend update status without refreshing the browser?**  
> *"The React frontend runs an active 2.5-second background polling cycle. When the backend daemon updates the tier in the database, the state updates automatically in real-time."*

---

*CloudVault — Built for Final Semester Evaluation Defense.*
