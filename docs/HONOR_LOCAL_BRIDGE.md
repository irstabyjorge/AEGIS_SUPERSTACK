# AEGIS Honor Local Bridge

Native Android application — not Termux.

- No INTERNET permission, root, background server, or broad storage permission.
- No `MANAGE_EXTERNAL_STORAGE`.
- User selects one folder using Android Storage Access Framework.
- Only the on-device shared-storage authority `com.android.externalstorage.documents` is accepted; cloud providers are rejected.
- Scope is the selected folder and its descendants, within this Android app profile.
- Recursively inventories metadata and SHA-256 hashes (bounded to 20,000 files / 40,000 visited entries / depth 32).
- Creates text files and edits text-like files up to 2 MiB with a second overwrite confirmation.
- Shares one selected file only through Android's visible share sheet after the user taps Share.
- Scan is an inventory/integrity operation, not antivirus. Indexed files are never executed.
- ChatGPT is not granted background access; a file reaches ChatGPT only if the user explicitly shares it.

Build: JDK 17, Android SDK Platform 35, Gradle 8.9, AGP 8.7.3.
Run: `gradle -p android/honor-local-bridge testDebugUnitTest assembleDebug`.
The CI workflow builds a debug APK artifact. This chat cannot install it on the handset or approve Android's folder permission prompt.
