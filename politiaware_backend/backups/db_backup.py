import os
import subprocess
import datetime
from politiaware_backend.backups.mega_helper import MegaHelper
from politiaware_backend.conf.conf_loader import config

class DBBackup:
    def __init__(self):     
        self.db_conf = config["database"]      
        # Mega path
        # self.mega_path = os.getenv("MEGA_DB_PATH", "/Backups/DB")
        # self.mega = mega

    def _git_commit(self):
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .decode("utf-8")
            .strip()
        )

    def _timestamp(self):
        return datetime.datetime.now().strftime("%Yy%mm%dd%Hh%Mm%Ss")

    def backup_db(self):
        filename = f"{self._git_commit()}_{self._timestamp()}_backup.sql"
        env = os.environ.copy()
        env["PGPASSWORD"] = self.password

        with open(filename, "w") as f:
            subprocess.run(
                [
                    "pg_dump",
                    "-U", self.db_conf['user'],
                    "-h", self.db_conf['host'],
                    "-p", self.db_conf['port'],
                    self.db,
                ],
                env=env,
                stdout=f,
                check=True,
            )

        self.mega.upload(filename, self.mega_path)
        print(f"✅ DB backup created and uploaded: {filename}")
        return filename

    def restore_db(self, filename):
        self.mega.download(f"{self.mega_path}/{filename}", ".")

        env = os.environ.copy()
        env["PGPASSWORD"] = self.password

        with open(filename, "r") as f:
            subprocess.run(
                [
                    "psql",
                    "-U", self.user,
                    "-h", self.host,
                    "-p", str(self.port),
                    "-d", self.db,
                ],
                env=env,
                stdin=f,
                check=True,
            )
        print(f"♻️  DB restored from {filename}")

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
            print(f"🗑️ Deleted old DB backup: {file}")

if __name__ == "__main__":
    db_backup = DBBackup()
    print(db_backup._git_commit())
    print(db_backup._timestamp())