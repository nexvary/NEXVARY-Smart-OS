from __future__ import annotations
from ..installer_engine.profiles import InstallationProfile, PACKAGES
from ..installer_engine.iso import ISOReport
import yaml

class AdapterError(ValueError):
    pass

def generate(profile: InstallationProfile, iso: ISOReport) -> tuple[str, str]:
    """Generate an interactive-storage seed. Never automate partition deletion."""
    profile.validate()
    if iso.distribution != profile.distribution or iso.checksum_status == "unverified":
        raise AdapterError("Matching distribution and verified ISO checksum required")
    packages = PACKAGES[profile.preset][profile.distribution]
    if profile.distribution == "ubuntu":
        if iso.installer != "subiquity-candidate":
            raise AdapterError("This Ubuntu image is not a supported Subiquity candidate")
        config = {"autoinstall": {"version": 1, "locale": profile.locale,
            "keyboard": {"layout": profile.keyboard}, "timezone": profile.timezone,
            "packages": packages, "interactive-sections": ["storage", "identity", "network"]}}
        # Identity remains interactive: do not store reusable passwords in profiles.
        return "autoinstall.yaml", yaml.safe_dump(config, sort_keys=False)
    if iso.installer != "debian-installer":
        raise AdapterError("Debian/Kali live images are not interchangeable with Debian Installer images")
    return "preseed.cfg", "\n".join([
        "# SMART OS preparation seed. Review storage and password interactively.",
        f"d-i debian-installer/locale string {profile.locale}",
        f"d-i keyboard-configuration/xkb-keymap select {profile.keyboard}",
        f"d-i time/zone string {profile.timezone}",
        f"d-i netcfg/get_hostname string {profile.hostname}",
        f"d-i passwd/username string {profile.username}",
        "d-i passwd/root-login boolean false",
        "d-i passwd/user-fullname string Smart OS User",
        f"d-i pkgsel/include string {' '.join(packages)}",
        "# No partman, format confirmations, bootloader target, or plaintext passwords.", ""])
