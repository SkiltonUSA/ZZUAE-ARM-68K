# Archive documentation refresh

Each current AmiPkg installer and component LHA contains:

- readme.txt: an exact byte copy of the main GitHub README.
- about.txt: the project title and existing credits/licensing acknowledgements.
- licence.txt: the project licence, or the existing mixed-component licence notices.

Original component licence files are retained. Root component-archive documents
are outside the application copyTree and do not add installed receipt entries.
The release checker compares all three documents with their source texts.

The JSON records identify the previous and refreshed archives, source document
hashes, component counts, and unchanged executable hashes. Catalogue signatures,
payload hashes and full LHA extraction round-trips pass. This refresh changes
no launcher/player binary, dependency policy, settings, firmware or application
version. It is not a new hardware or performance test. Existing source archives
remain the original release sources; main includes the updated packaging scripts.
