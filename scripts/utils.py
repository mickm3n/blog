import os


def find_md_files(root_dir):
    md_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".md"):
                md_files.append(os.path.join(root, file))
    return md_files
