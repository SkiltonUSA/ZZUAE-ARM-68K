# Release checklist

Before publishing a new release:

1. Increment the normal product version. Match the launcher, AmiPkg catalogue,
   release title/tag and main README; do not add a date to the release version.
2. Add a changelog entry describing new behaviour, fixes, compatibility changes
   and remaining limits. Distinguish newly implemented features from corrections
   to old documentation.
3. Update the main README feature/compatibility tables and download links.
   Link the user guide for each feature that needs setup instructions. Check
   launcher labels and help text against the same behaviour.
4. Record build inputs and SHA-256 hashes in an isolated release directory.
   Preserve installed/tested binaries; never reuse their output directory for
   experimental builds. Identify retained player/core builds explicitly.
5. Run relevant tests; distinguish native, instruction-model and physical tests.
   Do not present source availability or a passing build as hardware validation.
6. Verify dependency checks, signatures, archive contents and README links.
   Publish only after the release notes and main README describe that package.

Historical measurements retain their original build/version labels.

Run `python3 scripts/check_release_docs.py --launcher <release-executable>`
before packaging. Installer validation is a separate required check.
