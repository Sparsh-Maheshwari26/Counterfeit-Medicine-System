# Counterfeit Medicine System

A Streamlit student-project prototype for reviewing medicine label details against a public product-reference catalogue. The interface uses a blue healthcare dashboard style, a custom shield-and-capsule logo, and navigation for Overview, Verify Medicine, Medicine Database, and How It Works.

## Start the app on Windows

1. Install Python 3.10 or newer.
2. Extract this ZIP into a writable folder.
3. Double-click `run_windows.bat`. It creates a local `.venv`, installs dependencies and starts Streamlit. The first setup needs internet access.
4. If Windows blocks the batch file, open PowerShell in the project folder and run:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   python -m streamlit run app.py
   ```

5. Open the local URL printed by Streamlit, often `http://localhost:8501`.
6. Open **Medicine database** and choose **Sync 500 records** before a presentation if internet is available. The app stores downloaded reference records in `data/medicine_reference.db`.

## Prepare for a classroom presentation

Read [`PRESENTATION_GUIDE.md`](PRESENTATION_GUIDE.md) for a five-minute walkthrough, demo steps, viva answers and claims to avoid. The Verify Medicine page includes a **Load sample presentation case** button. The sample is fictional and is intended to demonstrate the user interface only.

For a presentation without reliable internet, sync the reference records before the event and keep `data/medicine_reference.db` in the project folder. The downloaded records stay local after the sync. If you do not sync records, explain that the app is in demo mode.

## Load 500 product listings from the terminal

From the project folder, run:

```powershell
python scripts/sync_reference_database.py --target 500
```

The sync script fetches 500 unique finished-product listings. It does not create fake rows to reach the requested count. If the source is unavailable or returns too few usable records, the sync fails without replacing existing official records.

## About the data

- Official reference provider: [openFDA Drug NDC Directory](https://open.fda.gov/apis/drug/ndc/).
- India-specific reference portal: [CDSCO approved drugs portal](https://www.cdscoonline.gov.in/CDSCO/cdscoDrugs/). Published quality-defect and spurious-drug reports are available at [CDSCO NSQ and spurious-drug alerts](https://cdscoonline.gov.in/CDSCO/viewPublicNSQDrug).
- The openFDA NDC Directory contains labeler-submitted listing information. A listing is not proof the FDA independently verified the submitted details, and an NDC listing is not itself a determination of FDA approval.
- The openFDA directory is US-focused. This prototype does not import the CDSCO database and should not be presented as a verified Indian medicine approval system.
- The included rows in `data/demo_medicines.csv` are clearly labelled fictional examples so the app remains interactive before the first network sync. They are not real medicine records and never return a genuine/authentic verdict.

## Important authenticity limitation

A public product catalogue usually contains product-level fields, not the secure manufacturing-batch history of each physical pack. This app checks product reference matches and date consistency only. It does not connect to manufacturer batch-verification APIs, traceability systems, QR/serialization services, or regulator case systems. A counterfeit pack might copy a real medicine's name and product code.

Use outputs such as **Reference found, batch unverified**, **No reference match**, or **Date warning**. Never report the pack as genuine based only on this prototype. For a real-world check, contact the manufacturer using its official contact details, ask a licensed pharmacist, or consult the relevant drug regulator.

## Main files

- `app.py`: Streamlit UI, navigation, screening logic, and results.
- `src/data_store.py`: SQLite schema, data loading, searching and persistence.
- `src/reference_sync.py`: openFDA fetch logic.
- `scripts/sync_reference_database.py`: CLI sync command.
- `assets/logo.svg` and `assets/logo.png`: custom project logo.
- `data/demo_medicines.csv`: fictional UI-only sample rows.
- `src/verification.py`: product-name and exact product-code matching helpers.
- `tests/test_verification.py`: offline tests for mismatch handling.
- `PRESENTATION_GUIDE.md`: five-minute demo outline and viva preparation.
- `presentation/Counterfeit_Medicine_System_Presentation.pptx`: editable 10-slide PowerPoint deck.

## Next steps for a production version

1. Obtain a valid data feed or API agreement for Indian medicine approvals and product identifiers.
2. Integrate an authorized batch-authentication endpoint from a manufacturer or serialization provider.
3. Add barcode/QR scanning, with cryptographic or server-side verification rather than relying on visible label text alone.
4. Add secure logs, rate limiting, monitoring, privacy review and independent validation.

## Simple result screen

The verification page now uses short result labels, a 0 to 100 rule-based screening score, a short list of issues, and simple field checks. The score is not a probability of authenticity and does not prove a medicine is genuine. A mismatch gives a Suspicious result; incomplete reference data gives Needs Checking; matching reference details give No Obvious Issue Found. Similar product listings are shown only as references to discuss with a pharmacist, not as a replacement recommendation.

The overview page has been simplified to one short description and two actions. Run the project with `python -m streamlit run app.py` or use `run_windows.bat`.
