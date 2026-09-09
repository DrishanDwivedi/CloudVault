# CloudVault Comprehensive Benchmark Results

Empirical benchmark evaluation of CloudVault tiered storage system across $N=5$ repetitions for 1 MB, 10 MB, and 100 MB objects on live Docker backends (**MinIO** Hot, **SeaweedFS** Warm, and **Garage S3** Archive).

---

## 1. Direct Storage Baseline Latency & Throughput (Bypassing API/DB)

| Backend Tier | Storage Target | Operation | Object Size | Mean Latency (ms) | Median Latency (ms) | P95 Latency (ms) | Throughput (MiB/s) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Hot** | MinIO | PUT | 1 MB | 4.56 | 2.35 | 11.88 | 219.33 |
| **Hot** | MinIO | GET | 1 MB | 9.74 | 9.78 | 10.37 | 102.72 |
| **Hot** | MinIO | PUT | 10 MB | 10.80 | 9.76 | 16.82 | 926.12 |
| **Hot** | MinIO | GET | 10 MB | 26.06 | 23.88 | 33.70 | 383.69 |
| **Hot** | MinIO | PUT | 100 MB | 1,079.49 | 929.79 | 1,830.34 | 92.64 |
| **Hot** | MinIO | GET | 100 MB | 123.95 | 108.97 | 203.76 | 806.79 |
| **Warm** | SeaweedFS | PUT | 1 MB | 2.04 | 2.27 | 2.73 | 490.79 |
| **Warm** | SeaweedFS | GET | 1 MB | 19.50 | 18.61 | 25.06 | 51.29 |
| **Warm** | SeaweedFS | PUT | 10 MB | 534.99 | 8.37 | 2,054.16 | 18.69 |
| **Warm** | SeaweedFS | GET | 10 MB | 29.34 | 30.60 | 35.37 | 340.80 |
| **Warm** | SeaweedFS | PUT | 100 MB | 2,269.91 | 1,206.13 | 4,637.30 | 44.05 |
| **Warm** | SeaweedFS | GET | 100 MB | 136.51 | 119.32 | 205.63 | 732.52 |
| **Archive** | Garage S3 | PUT | 1 MB | 1.57 | 1.64 | 2.03 | 636.38 |
| **Archive** | Garage S3 | GET | 1 MB | 17.81 | 19.66 | 21.53 | 56.13 |
| **Archive** | Garage S3 | PUT | 10 MB | 7.05 | 7.55 | 9.00 | 1,417.72 |
| **Archive** | Garage S3 | GET | 10 MB | 20.75 | 20.36 | 22.83 | 481.93 |
| **Archive** | Garage S3 | PUT | 100 MB | 1,390.34 | 1,229.45 | 2,381.80 | 71.92 |
| **Archive** | Garage S3 | GET | 100 MB | 108.89 | 100.11 | 153.85 | 918.38 |

---

## 2. CloudVault-Mediated API Operations (Full Stack Lifecycle)

| Operation | Object Size | Mean Latency (ms) | Median Latency (ms) | P95 Latency (ms) | Throughput (MiB/s) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Mediated PUT** (+DB+SHA256) | 1 MB | 122.31 | 108.76 | 176.83 | 8.18 |
| **Mediated GET** (+DB+SHA256) | 1 MB | 113.77 | 114.70 | 127.32 | 8.79 |
| **Mediated PUT** (+DB+SHA256) | 10 MB | 109.62 | 109.18 | 123.00 | 91.22 |
| **Mediated GET** (+DB+SHA256) | 10 MB | 140.28 | 137.84 | 149.96 | 71.29 |
| **Mediated PUT** (+DB+SHA256) | 100 MB | 2,020.30 | 1,018.83 | 4,899.90 | 49.50 |
| **Mediated GET** (+DB+SHA256) | 100 MB | 343.01 | 348.22 | 377.42 | 291.54 |

---

## 3. Application Layer Overhead

$$\text{Relative Overhead (\%)} = \frac{\text{Mediated Latency} - \text{Direct Latency}}{\text{Direct Latency}} \times 100$$

| Operation | Object Size | Direct Baseline (ms) | Mediated API (ms) | Absolute Overhead (ms) | Relative Overhead (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **PUT** | 1 MB | 4.56 | 122.31 | +117.75 | **+2,582.6%** |
| **GET** | 1 MB | 9.74 | 113.77 | +104.03 | **+1,068.6%** |
| **PUT** | 10 MB | 10.80 | 109.62 | +98.82 | **+915.2%** |
| **GET** | 10 MB | 26.06 | 140.28 | +114.22 | **+438.2%** |
| **PUT** | 100 MB | 1,079.49 | 2,020.30 | +940.81 | **+87.2%** |
| **GET** | 100 MB | 123.95 | 343.01 | +219.06 | **+176.7%** |

*Note: Base overhead of ~100–120 ms consists of ORM database session transaction management and synchronous SHA-256 calculation. As payload size increases, raw storage I/O dominates.*

---

## 4. Multi-Tier Lifecycle Migration Latency & Throughput

Complete pipeline: Source Read $\rightarrow$ Destination Write $\rightarrow$ SHA-256 Verification $\rightarrow$ Source Purge $\rightarrow$ Metadata Update.

| Lifecycle Transition | Object Size | Mean Latency (ms) | Median Latency (ms) | P95 Latency (ms) | Throughput (MiB/s) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Hot $\rightarrow$ Warm** (MinIO $\rightarrow$ SeaweedFS) | 1 MB | 891.96 | 792.51 | 1,248.83 | 1.12 |
| **Hot $\rightarrow$ Warm** (MinIO $\rightarrow$ SeaweedFS) | 10 MB | 1,012.25 | 1,052.82 | 1,159.84 | 9.88 |
| **Hot $\rightarrow$ Warm** (MinIO $\rightarrow$ SeaweedFS) | 100 MB | 3,008.09 | 2,865.94 | 3,958.69 | 33.24 |
| **Warm $\rightarrow$ Archive** (SeaweedFS $\rightarrow$ Garage S3) | 1 MB | 999.03 | 822.00 | 1,577.35 | 1.00 |
| **Warm $\rightarrow$ Archive** (SeaweedFS $\rightarrow$ Garage S3) | 10 MB | 1,481.33 | 1,502.76 | 2,153.22 | 6.75 |
| **Warm $\rightarrow$ Archive** (SeaweedFS $\rightarrow$ Garage S3) | 100 MB | 2,474.27 | 2,437.92 | 2,863.15 | 40.42 |

---

## 5. Worker Concurrency Scaling (Batch Migration Throughput)

Batch migration workload: **16 files $\times$ 5 MB** (80 MB total payload) migrating Hot (MinIO) $\rightarrow$ Warm (SeaweedFS) across worker thread counts $W \in [1, 2, 4, 8]$.

| Concurrent Workers ($W$) | Total Batch Duration | Avg Latency / File | Aggregate Throughput | Speedup Factor | Parallel Efficiency | Success Rate |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1 Worker** | 8.46 s | 528.7 ms | 9.46 MiB/s | **1.00x** | **100.0%** | 16/16 (100%) |
| **2 Workers** | 10.17 s | 635.8 ms | 7.86 MiB/s | **0.83x** | **41.6%** | 16/16 (100%) |
| **4 Workers** | 9.26 s | 578.9 ms | 8.64 MiB/s | **0.91x** | **22.8%** | 16/16 (100%) |
| **8 Workers** | 9.45 s | 590.9 ms | 8.46 MiB/s | **0.89x** | **11.2%** | 16/16 (100%) |

*Key Findings*: Under single-host Docker networking and disk I/O constraints, aggregate storage throughput stabilizes around 8.5–9.5 MiB/s across all concurrency tiers with 100% data integrity and zero race-condition lock collisions.