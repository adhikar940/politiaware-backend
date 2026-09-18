#!/usr/bin/env python
import os
import json
import subprocess
from collections import defaultdict

# ✅ Setup Django (adjust `yourproject.settings`)
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "m.settings")
django.setup()


def get_model_dependencies():
    """Build dependency graph {model: [parent_models]} from ForeignKeys."""
    from django.apps import apps
    deps = defaultdict(list)
    for model in apps.get_models():
        label = f"{model._meta.app_label}.{model._meta.model_name}"
        for field in model._meta.fields:
            if field.is_relation and field.related_model:
                parent = f"{field.related_model._meta.app_label}.{field.related_model._meta.model_name}"
                if parent != label:
                    deps[label].append(parent)
    return deps


def topo_sort(models, deps):
    """Topological sort so parents load before children."""
    result, visited = [], {}

    def visit(m):
        if visited.get(m) == "temp":
            return  # cycle
        if visited.get(m) == "perm":
            return
        visited[m] = "temp"
        for p in deps.get(m, []):
            if p in models:
                visit(p)
        visited[m] = "perm"
        result.append(m)

    for m in models:
        visit(m)
    return result


def safe_loaddata_by_model(fixture_path, verbosity=2):
    """Split fixture by model and load in FK dependency order."""
    if not os.path.exists(fixture_path):
        raise FileNotFoundError(f"{fixture_path} not found")

    with open(fixture_path) as f:
        data = json.load(f)

    grouped = defaultdict(list)
    for obj in data:
        grouped[obj["model"]].append(obj)

    deps = get_model_dependencies()
    ordered_models = topo_sort(list(grouped.keys()), deps)

    os.makedirs("_split_fixtures", exist_ok=True)

    for model in ordered_models:
        objs = grouped[model]
        if not objs:
            continue
        filename = os.path.join("_split_fixtures", f"{model.replace('.', '_')}.json")
        with open(filename, "w") as out:
            json.dump(objs, out, indent=2)

        print(f"▶ Loading {len(objs)} objects for {model}...")
        try:
            subprocess.run(
                ["python", "manage.py", "loaddata", filename, f"--verbosity={verbosity}", "--traceback"],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed on {model}: {e}")
            break

    print("✅ Done loading fixtures.")



if __name__ == "__main__":
    fixture_path = "/media/mohan/mn/adhikar/adhikar-docker-compose/m/m/data.json"
    safe_loaddata_by_model(fixture_path, verbosity=3)
