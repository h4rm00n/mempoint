import os

dirs = [
    "backend/app/api",
    "backend/app/core",
    "backend/app/memory",
    "backend/app/models",
    "backend/app/services",
    "backend/app/utils",
    "backend/data/milvus",
    "backend/data/kuzu",
    "backend/tests",
    "frontend",
    "docs"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"Created: {d}")
