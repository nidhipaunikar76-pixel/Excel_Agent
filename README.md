# Autonomous AI Excel Automation Agent

A production-grade, privacy-preserving AI Agent framework engineered to interpret, edit, update, format, and audit Microsoft Excel (`.xlsx`) data sheets using localized natural language commands. 

This project bridges unstructured human instructions with structured programmatic spreadsheet manipulation models.

## Core Engineering Capabilities
- **Natural Language Schema Formatting:** Automatically parses textual human requests (e.g., *"Highlight high complexities in soft red and calculate a weekly velocity total row"*) and compiles them into functional programmatic cell adjustments.
- **Data Security & Fallback Guardrails:** Automatically creates snapshot safety copies of target files within a localized `excel_backups/` cache directory before any edit function is executed to prevent real-world database loss.
- **Enterprise-Grade Governance Auditing:** Tracks execution pipelines, tracking timestamps, user parameters, and modified row indices programmatically into `excel_agent_audit.json` for security compliance reviews.
- **Zero-Hardcoding Flexibility:** Designed to dynamically parse data fields and spreadsheet schemas at runtime based on the spreadsheet provided.
- **One-Click Local Launch:** Includes custom initialization setup tools (`start_agent.bat`) for easy local deployment on Windows setups.

##  Repository Architecture Blueprint
```text
excelagent/
│
├── .gitignore               # Restricts sensitive excel_backups/ from leaking public histories
├── requirements.txt         # Package dependencies (openpyxl, ollama)
├── app.py                   # Master AI Execution Orchestration Loop
├── excel_agent_audit.json   # Structural enterprise compliance event log registry
├── start_agent.bat          # Automated startup utility launch script
└── README.md                # System engineering architecture manual
```

## Local System Installation & Run Guide

1. **Verify that your local Ollama client engine is initialized and listening:**
   ```bash
   ollama run llama3.2
   ```

2. **Clone this workspace repository and install package dependencies:**
   ```bash
   pip install openpyxl ollama pandas
   ```

3. **Launch the dynamic automation agent loop:**
   ```bash
   python app.py
   ```
   *Alternatively, double-click the `start_agent.bat` script on Windows computers to spin up the runtime engine dashboard instantly.*
