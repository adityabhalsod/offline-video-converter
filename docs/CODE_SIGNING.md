# Code signing for Windows

Windows shows "Windows protected your PC" (SmartScreen) and some antivirus tools
flag downloads that are **unsigned** or come from a publisher with **no reputation
yet**. Signing the `.exe` and the installer with a certificate from a trusted
authority fixes the first part and lets reputation build up over downloads.

Things signing does **not** do:

- A self-signed certificate does nothing for SmartScreen. Only certificates from a
  public certificate authority count.
- Even a real certificate (including EV) no longer removes the warning on day one.
  Since 2024 SmartScreen builds reputation per publisher from download volume, so the
  first releases may still show a warning for a while. Signed releases keep that
  reputation from one version to the next; unsigned ones start from zero every time.

## How the Release workflow signs

`.github/workflows/release.yml` signs through [SignPath](https://signpath.io) when the
settings below exist, and builds unsigned (as before) when they don't. On Windows it:

1. builds `OfflineVideoConverter.exe` with PyInstaller (with icon and version info),
2. sends that exe to SignPath and puts the signed copy back,
3. builds the installer from the signed app, so the installed exe is signed too,
4. sends the installer to SignPath and attaches the signed installer to the release,
5. checks both signatures with `Get-AuthenticodeSignature` and fails if either is invalid.

Only our own executable and installer are signed. The bundled FFmpeg binaries are
third-party and are shipped as they come.

### Repository settings

In GitHub: **Settings, Secrets and variables, Actions**.

| Kind | Name | Value |
| --- | --- | --- |
| Secret | `SIGNPATH_API_TOKEN` | API token of a SignPath CI user that has *submitter* rights |
| Variable | `SIGNPATH_ORGANIZATION_ID` | Your SignPath organization ID |
| Variable (optional) | `SIGNPATH_PROJECT_SLUG` | Defaults to `offline-video-converter` |
| Variable (optional) | `SIGNPATH_POLICY_SLUG` | Defaults to `release-signing` |

### SignPath project settings

- Project slug: `offline-video-converter`, connected to this GitHub repository as a
  trusted build system (GitHub.com).
- Artifact configuration `app-exe`: contents of `packaging/signing/signpath-app-exe.xml`.
- Artifact configuration `installer`: contents of `packaging/signing/signpath-installer.xml`.
- Signing policy slug: `release-signing`.

If a signing policy needs manual approval, the workflow waits up to an hour for you to
approve each request in SignPath.

## Free option for this project: SignPath Foundation

[SignPath Foundation](https://signpath.org) signs open source projects for free. The
certificate's publisher name is **"SignPath Foundation"**, not your own name.

Conditions (from <https://signpath.org/terms>), which this project mostly meets already:

- OSI-approved license with no commercial dual licensing (Apache 2.0 is fine).
- No malware or hacking tools; you only sign your own project's binaries.
- The project is actively maintained and already has a release.
- MFA turned on for your GitHub and SignPath accounts.
- A "Code signing policy" section on the README and the release page, including the
  line *"Free code signing provided by SignPath.io, certificate by SignPath Foundation"*
  (add it once you are accepted; a draft is below).
- Every release is approved by hand in SignPath.

Apply at <https://signpath.org/apply>. Acceptance is at their discretion.

Draft README section for after acceptance:

```markdown
## Code signing policy

Free code signing provided by [SignPath.io](https://signpath.io), certificate by
[SignPath Foundation](https://signpath.org).

- Committers and reviewers: [adityabhalsod](https://github.com/adityabhalsod)
- Approvers: [adityabhalsod](https://github.com/adityabhalsod)

This program will not transfer any information to other networked systems unless
specifically requested by the user or the person installing or operating it.
```

## Paid options with your own name on the certificate

- **Certum Open Source Code Signing (cloud, about EUR 49 per year).** Issued to an
  individual as "Open Source Developer, <your name>" after an identity check. The key
  lives in Certum's SimplySign cloud and each session is unlocked with a code from their
  phone app, so it does not fit an unattended CI run. Practical use: run the Release
  workflow with *publish* unticked, download the build, sign the exe and installer on
  your PC with `signtool` while SimplySign Desktop is connected, then upload them.
- **Azure Artifact Signing (formerly Trusted Signing), from USD 9.99 per month.** The
  easiest to automate, but at the time of writing Microsoft only onboards individual
  developers in the US and Canada, and organizations with three years of verifiable
  history in a few regions.
- **Standard (OV) certificates from other authorities, roughly EUR 200 to 500 per year.**
  Since 2023 the private key must be kept on a hardware token or cloud HSM, so a plain
  `.pfx` file in a GitHub secret is no longer possible for new certificates.

## Reporting a false positive

If an antivirus flags a release, submit the file as a false positive (for Microsoft
Defender: <https://www.microsoft.com/wdsi/filesubmission>). PyInstaller apps are a
common false-positive target; signing reduces this.
