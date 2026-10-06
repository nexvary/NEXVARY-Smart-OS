# Security model

The GUI does not require permanent administrator privileges. Hardware inspection and diagnostics are local. No serials, device IDs or machine fingerprints are sent to a service. User-selected ISO downloads contact only the allowlisted official HTTPS distribution domains, including redirect targets. The Debian-listed ftp.acc.umu.se mirror and its named server subdomains are allowlisted to handle official cdimage redirects. Mirror provenance: https://www.debian.org/CD/http-ftp/.

Downloads require a supplied SHA256; data goes to a temporary file, has a size limit, is hashed during transfer and is published without overwriting an existing destination. Hash provenance and signed checksum catalogs are not yet verified automatically. Never treat a hash alone as proof of publisher authenticity.

All external commands use argv arrays and shell=False. PowerShell scripts are fixed; any dynamic literal must escape single quotes. PnPUtil backup accepts only `*` or an `oem<number>.inf` published name. Profiles validate schema, distribution, hostname, username, timezone, locale, keyboard and named preset before configuration generation. No passwords or arbitrary post-install scripts are accepted.

JSON diagnostic exports redact serial/identifier/credential keys recursively. Operation journals record operation/status without raw command output. Error-log analysis emits categorized findings rather than persisting source content. Raw hardware IDs are deliberately visible in the local device detail view.

USB writes are CLI-only and Linux-only, with narrow root use, positive USB/removable identification, stable serial, protected-partition exclusion, exact confirmation, hash verification, recheck and O_EXCL/O_NOFOLLOW open. There is no automatic unmount or partition deletion. Physical-media and hotplug race tests are still required before release. Raw writes have no guaranteed rollback.

No Windows driver install/restore, firmware update, disk formatting or partition resize is enabled. Those features need actual signature/catalog/native compatibility and recovery verification, not confidence inferred by AI.
