import os
import subprocess
import datetime
import shutil
from .mega_helper import MegaHelper


class MediaBackup:
    def __init__(self, mega: MegaHelper):
        # Local media
        self.media_root = os.getenv("DJANGO_MEDIA_ROOT", "media")

        # Mega path
        self.mega_path = os.getenv("MEGA_MEDIA_PATH", "/Backups/Media")

        self.mega = mega

    def _git_commit(self):
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
            .decode("utf-8")
            .strip()
        )

    def _timestamp(self):
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    def backup_media(self):
        filename = f"{self._git_commit()}_{self._timestamp()}_media_backup.tar.gz"
        shutil.make_archive(filename.replace(".tar.gz", ""), "gztar", self.media_root)

        self.mega.upload(filename, self.mega_path)
        print(f"✅ Media backup created and uploaded: {filename}")
        return filename

    def restore_media(self, filename):
        self.mega.download(f"{self.mega_path}/{filename}", ".")
        shutil.unpack_archive(filename, self.media_root)
        print(f"♻️  Media restored from {filename}")

    def list_backups(self):
        return self.mega.list_files(self.mega_path)

    def latest_backup(self):
        backups = self.list_backups()
        return sorted(backups)[-1] if backups else None

    def cleanup_old_backups(self, keep_last_n=5):
        backups = sorted(self.list_backups())
        old = backups[:-keep_last_n] if len(backups) > keep_last_n else []
        for file in old:
            self.mega.delete(f"{self.mega_path}/{file}")
            print(f"🗑️ Deleted old media backup: {file}")
