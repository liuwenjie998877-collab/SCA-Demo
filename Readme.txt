========================================================================
🟢 SupplyChain Alpha (SCA) 2.0 - Green Supply Chain Finance Gateway
========================================================================

Dear Professor / Review Committee,

This package contains the source code and underlying quantitative model documentation for the [SupplyChain Alpha (SCA)] project, an entry for the HKTech 300 program.

SCA is designed to bridge the gap between small-to-medium manufacturing exporters and global financial institutions in the face of the EU Carbon Border Adjustment Mechanism (CBAM). By integrating Generative AI (for automated document auditing) with Blockchain (for immutable verification), we provide a low-cost, automated gateway for joint ESG auditing and dynamic credit risk pricing.

------------------------------------------------------------------------
📂 【Part I】 Getting Started (SCA 2.0 Interactive Frontend)
------------------------------------------------------------------------
The main program `app_ui.py` demonstrates the system's interactive logic, data workflow, and anti-tampering mechanism.

1. Dependencies:
   - Python 3.9 or higher is recommended.
   - Install required packages via terminal/command prompt:
     pip install streamlit google-genai

2. Running the System:
   - Navigate to the project directory and run:
     python -m streamlit run app_ui.py
   - The system will automatically open the demo interface in your default browser.

3. Suggested Demo Walkthrough:
   - [Step 1] Globalization: Use the sidebar to toggle between English, Simplified Chinese, and Traditional Chinese.
   - [Step 2] Data Ingestion: Drag and drop a test invoice PDF. The AI Agent acts as a decentralized oracle to extract supply chain metadata.
   - [Step 3] Dual-Panel Audit: Experience the "Bank-Supplier" unified view.
              (Left) 🏭 Supplier Node: Displaying extracted data with blockchain-anchored proof.
              (Right) 🏦 Banker Credit Engine: Displaying real-time ESG credit rating and loan status.
   - [Step 4] Immutable Audit Trail: Click "Commit & Next Transaction" to return to the dashboard. The bottom section displays a blockchain-style ledger capturing the transaction hash.
