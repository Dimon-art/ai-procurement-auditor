from datetime import datetime
from pathlib import Path

import zipfile


BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "db.sqlite3"
MEDIA_DIR = BASE_DIR / "media"
BACKUP_DIR = BASE_DIR / "backups"


def create_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"backup_{timestamp}.zip"

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(
        backup_file,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        if DB_FILE.exists():
            archive.write(
                DB_FILE,
                arcname="db.sqlite3",
            )

        if MEDIA_DIR.exists():
            for file_path in MEDIA_DIR.rglob("*"):
                if file_path.is_file():
                    archive.write(
                        file_path,
                        arcname=file_path.relative_to(BASE_DIR),
                    )

    return backup_file


if __name__ == "__main__":
    backup = create_backup()
    print(f"Backup created: {backup}")
