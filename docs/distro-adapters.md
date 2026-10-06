# Linux adapter guide

An adapter must declare supported ISO structure, distribution, installer and version capabilities. Never equate a distribution name with a single installer implementation.

Current preparation support:

| Distribution | Evidence | Output | Interactive safeguards |
|---|---|---|---|
| Debian | `.disk/info` plus `install.amd/` | `preseed.cfg` | Partitioning, passwords, boot target |
| Kali | `.disk/info` plus `install.amd/` | `preseed.cfg` | Partitioning, passwords, boot target |
| Ubuntu | `.disk/info` plus `casper/install-sources.yaml` | `autoinstall.yaml` candidate | Storage, identity, network |

The current seed is a preparation artifact, not a complete unattended image. On Ubuntu, hostname/username from the saved profile are not injected while identity stays interactive. Debian preset packages do not themselves guarantee a desktop; distribution defaults/task selection still apply. No custom scripts are accepted in this alpha.

Use SHA256 authenticated from the distribution. GPG signature validation of SHA256SUMS is pending. Live/Calamares images are not silently treated as Debian Installer. Fedora/Kickstart, openSUSE/AutoYaST and Arch/archinstall should be separate adapters with their own integration tests.

Relevant primary references:
- https://canonical-subiquity.readthedocs-hosted.com/en/latest/reference/autoinstall-reference.html
- https://canonical-subiquity.readthedocs-hosted.com/en/latest/tutorial/providing-autoinstall.html
- https://www.debian.org/releases/stable/amd64/apb.en.html
- https://www.kali.org/docs/installation/
