import os
import sys
import zlib

def list_branches(repo_path):
    heads_path = os.path.join(repo_path, ".git", "refs", "heads")
    if not os.path.isdir(heads_path):
        print("Не найден репозиторий Git:", repo_path)
        return
    for name in os.listdir(heads_path):
        print(name)

def read_git_object(repo_path, sha):
    obj_path = os.path.join(repo_path, ".git", "objects", sha[:2], sha[2:])
    with open(obj_path, "rb") as f:
        compressed = f.read()
    raw = zlib.decompress(compressed)
    header, _, body = raw.partition(b'\x00')
    kind, _ = header.split()
    return kind.decode(), body.decode()

def show_last_commit(repo_path, branch):
    ref_path = os.path.join(repo_path, ".git", "refs", "heads", branch)
    if not os.path.exists(ref_path):
        print(f"Ветка '{branch}' не найдена")
        return
    with open(ref_path, "r") as f:
        commit_sha = f.read().strip()

    kind, body = read_git_object(repo_path, commit_sha)
    if kind != "commit":
        print("Объект не является коммитом:", commit_sha)
        return

    print(body.strip())

if len(sys.argv) < 2:
    print("Нет пути к репозиторию")
elif len(sys.argv) == 2:
    repo_path = sys.argv[1]
    list_branches(repo_path)
else:
    repo_path = sys.argv[1]
    branch = sys.argv[2]
    show_last_commit(repo_path, branch)