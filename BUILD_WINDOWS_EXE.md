# Build the actual Windows desktop EXE

The app is designed to run as a native desktop window using pywebview when packaged. The normal client does **not** need Python, CMD, Node, VS Code, or a browser.

## GitHub Actions
1. Put this folder in a GitHub repository.
2. Open Actions -> Build National Pathology Lab Windows EXE.
3. Click Run workflow.
4. Download the `NationalPathologyLab-Windows-EXE` artifact.
5. Extract it and double-click `NationalPathologyLab.exe`.

The packaged app stores its database and uploaded signature under the Windows Local AppData folder so it does not require admin permission.
