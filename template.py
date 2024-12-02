import os
from pathlib import Path

list_of_files = [
    f"us_visa/__init__.py",
    f"us_visa/cloud_storage/__init__.py",
    f"us_visa/components/__init__.py",
    f"us_visa/configuration/__init__.py",
    f"us_visa/constants/__init__.py",
    f"us_visa/data_access/__init__.py",
    f"us_visa/entity/__init__.py",
    f"us_visa/exceptions/__init__.py",
    f"us_visa/logger/__init__.py",
    f"us_visa/pipeline/__init__.py",
    f"us_visa/utils/__init__.py"
]

for filepath in list_of_files:
    filepath = Path(filepath)
    filedir, filename = os.path.split(filepath)
    if filedir != "":
        os.makedirs(filedir, exist_ok=True)
    if (not os.path.exists(filepath)) or (os.path.getsize(filepath) == 0):
        with open(filepath, "w") as f:
            pass
    else:
        print(f"file is already present at: {filepath}")