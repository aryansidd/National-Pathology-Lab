# National Pathology Lab - FINAL v6

- Native desktop-window mode when packaged as EXE (pywebview).
- Client does not need Python/Node/VS Code/browser after receiving the EXE.
- One test/report per A4 PDF page: CBC page, LFT page, TIBC page, etc.
- Report table order: Parameter | Result | Flag | Unit | Reference Range.
- Fixed column widths prevent overlap.
- HIGH/LOW auto flagging remains enabled.
- Bill remains a separate small receipt-style PDF.
- QR code can open the full report URL configured in Lab Settings.

For a native Windows EXE, use `.github/workflows/build-windows.yml` or build on Windows with PyInstaller.
