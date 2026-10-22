# AI-Enhanced IP KVM & Remote Server Monitoring

An open-source, low-cost IP KVM appliance built on a **Raspberry Pi 5**, combining low-level hardware access (BIOS-level video capture and USB keyboard/mouse emulation) with automated telemetry baseline learning and AI-powered anomaly explanations via Google Gemini.

Developed as a capstone project by **Team Alpha**, a four-person team:
* **Harvey Wyche** – All software in this repository, including machine-learning baselines, AI integration, and the web monitoring interface.
* **Three additional team members** – Hardware assembly and enclosure fabrication; dashboard design and visualization; and security testing and access-control contributions.

---

## Key Features

- **Low-Level Hardware Access:** Captures target server HDMI output via a USB capture adapter and emulates standard Human Interface Devices (HID) over USB-C gadget mode to reach BIOS/UEFI settings.
- **Automated Baseline Learning:** Continuously polls system health metrics (CPU, memory, disk, temperature, uptime) to build statistical operational baselines.
- **AI-Driven Anomaly Detection:** Detects performance drift and queries Google Gemini to translate raw statistical outliers into plain-text explanations and actionable remediation steps.
- **Dual Dashboards:**
  - **Local Console:** BTT 7-inch touchscreen for local health and alert status.
  - **Web Dashboard:** Secure, authenticated browser-based interface providing live video streaming, historical telemetry charts, and audit logs.
- **Edge-First Architecture:** Local storage handled via a lightweight SQLite database with a 24-hour rotating buffer. External API calls to Gemini occur strictly upon anomaly detection.

---

## System Architecture

```text
+-------------------------------------------------------------------------+
|                             TARGET SERVER                               |
|   (Sends Video via HDMI Out / Receives Input via USB Emulation / Runs   |
|                          Telemetry Agent)                               |
+--------------------+--------------------------------+-------------------+
                     | (HDMI Capture & USB Gadget)    | (Periodic Metrics)
                     v                                v
+-------------------------------------------------------------------------+
|                   RASPBERRY PI 5 CENTRAL APPLIANCE                      |
|                                                                         |
|   +-----------------------+     +-----------------------------------+   |
|   |   IP KVM Service      |     |  Data Collector & Anomaly Engine  |   |
|   |  (Video Stream & HID) |     | (Learns Baseline / Detects Drift) |   |
|   +-----------+-----------+     +-----------------+-----------------+   |
|               |                                   |                     |
|               |                                   v                     |
|               |                      +--------------------------+       |
|               |                      | Gemini 3.5 Flash-Lite    |       |
|               |                      | (Plain Text Explanations)|       |
|               |                      +------------+-------------+       |
|               v                                   v                     |
|   +-----------------------+     +-----------------------------------+   |
|   | Local SQLite Database |<----+ Timestamped Metrics, Event Logs,  |   |
|   | (24-Hour Buffer)      |     | & Anomaly Results                 |   |
|   +-----------+-----------+     +-----------------------------------+   |
+---------------+-----------------------------------+---------------------+
                |                                   |
                v (Local HDMI Display)              v (HTTPS / Encrypted VPN)
+-------------------------------+   +-------------------------------------+
| BTT 7-INCH TOUCHSCREEN        |   | REMOTE WEB DASHBOARD                |
| (Local Status, Health, Alert) |   | (Live Feed, Telemetry Charts, Logs) |
+-------------------------------+   +-------------------------------------+
```

---

## Tech Stack

- **Hardware:** Raspberry Pi 5, BTT 7-Inch HDMI Touchscreen, USB-to-HDMI Capture Adapter, USB-C Power/Data Splitter, 3D Printed PETG Enclosure.
- **Software & Backend:** Python, SQLite, Linux OS, USB Gadget drivers.
- **AI & Analytics:** Scikit-learn, River (streaming ML), Google Gemini API.
- **Security:** TLS encryption, session authentication, NIST SP 800-53 aligned access controls.

---

## Repository Structure

```text
.
├── .gitignore
├── LICENSE
├── README.md
├── monitor/                  # Local metrics collection, anomaly detection, and dashboard
└── worker/                   # Cloudflare Worker API and database schema
```

---

## Getting Started

1. **Hardware Setup:** Connect the target machine's video output to the HDMI capture card and configure USB gadget mode for keyboard/mouse emulation.
2. **Install and configure:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
   The local SQLite database is created automatically when the monitor starts. To enable Gemini explanations and cloud reporting, follow the setup in [`worker/README.md`](worker/README.md), then set your deployed Worker URL in `monitor/cloud_sender.py`. Keep API keys in Cloudflare Worker secrets; never commit credentials.
3. **Run the monitor:** Start the local dashboard with:
   ```bash
   python monitor/app.py
   ```
   Open `http://127.0.0.1:5000` and start monitoring from the dashboard.

---

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.