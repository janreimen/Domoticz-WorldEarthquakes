import os
import tarfile

PLUGIN_NAME = "Domoticz-WorldEarthquakes"
VERSION = "0.1.1"
OUTPUT_TAR = f"{PLUGIN_NAME}-v{VERSION}.tar.gz"

EXCLUDE_FILES = {
    OUTPUT_TAR,
    ".git",
    ".github",
    "tests",
    "tools",
    ".gitignore",
    "checklist.md",
    "deploy.md",
    "accessibility.md",
    "roadmap.md",
    "requirements.txt",
}

def package_plugin():
    with tarfile.open(OUTPUT_TAR, "w:gz") as tar:
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_FILES and not d.startswith(".")]
            for file in files:
                if file in EXCLUDE_FILES or file.endswith(".pyc"):
                    continue
                file_path = os.path.join(root, file)
                archive_name = os.path.relpath(file_path, ".")
                tar.add(file_path, arcname=archive_name)

if __name__ == "__main__":
    package_plugin()
