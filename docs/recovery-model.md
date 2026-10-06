# Recovery model

ISO preparation never edits the source image. Download failures remove the incomplete temporary image. A changed image or disk snapshot invalidates the USB plan. USB verification failure marks the written medium unusable; it does not claim successful recovery. Raw overwrites cannot restore erased data, hence all disk-selection safeguards are mandatory.

Driver exports are kept in a new folder with a manifest after success. A failed export may leave a partial folder but no valid completion state. The manifest verifies contents before matching. Backup integrity alone never enables installation. Restore, rollback and restore-point creation are pending native Windows implementation and VM validation.

Installer logs yield deterministic findings and reviewable suggestions. No GRUB, EFI, repository, DNS or dependency repair runs in this alpha. No checkpoint may report resumability without probing the target installation state. Future recovery must record verified checkpoints and recovery outcomes rather than marking a command exit as repaired.
