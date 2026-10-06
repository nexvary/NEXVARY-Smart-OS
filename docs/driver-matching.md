# Driver matching architecture

Windows inventory comes from CIM Win32_PnPEntity and Win32_PnPSignedDriver. Missing means ConfigManagerErrorCode 28. Other problem codes require review. Installed does not mean latest or recommended.

Local preview reads NTamd64 INF model IDs. Exact Hardware ID match outranks Compatible ID match. Unsupported architecture and unmatched devices are rejected. Signature-not-verified candidates are never eligible; the parser does not set signature trust. Version/date has no automatic priority. Provider strings and INF comments cannot establish trust.

This is not full INF parsing or Microsoft's driver rank. Manufacturer section references, decorated OS/build constraints, extension/component dependencies, catalog member hashes, trusted signer/kernel policy, OEM suitability and native PnP rank must be implemented before enabling install. A plain SHA256 backup manifest can detect accidental corruption but can be recreated by an attacker; it is not a signature.

Safe installation contract for the next milestone: verified package and source; exact current device/OS; native rank; current-driver export; verified recovery/restore-point availability where required; explicit review; one narrowly elevated operation; post-install error-code and version inspection; actual rollback if validation fails. Do not install BIOS or firmware automatically. No installer command is exposed by this alpha.
