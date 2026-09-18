import subprocess


class MegaHelper:
    """Helper for Mega login and file operations."""

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self._login()

    def _login(self):
        subprocess.run(
            ["mega-login", self.email, self.password],
            check=True,
        )

    def list_files(self, path: str):
        result = subprocess.check_output(["mega-ls", path]).decode("utf-8").strip()
        files = [line.strip() for line in result.split("\n") if line.strip()]
        return files

    def upload(self, local_file: str, remote_path: str):
        subprocess.run(["mega-put", local_file, remote_path], check=True)

    def download(self, remote_file: str, dest_dir: str = "."):
        subprocess.run(["mega-get", remote_file, dest_dir], check=True)

    def delete(self, remote_file: str):
        subprocess.run(["mega-rm", remote_file], check=True)
