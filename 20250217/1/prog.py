import os
import sys

def list_branches(repo_path):
    heads_path = os.path.join(repo_path, ".git", "refs", "heads")
    if not os.path.isdir(heads_path):
        print("Не найден репозиторий Git:", repo_path)
        return
    for name in os.listdir(heads_path):
        print(name)

if len(sys.argv) < 2:
    print("Нет пути к репозиторию")
else:
    repo_path = sys.argv[1]
    list_branches(repo_path)