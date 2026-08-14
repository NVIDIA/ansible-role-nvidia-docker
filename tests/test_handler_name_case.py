"""Regression test: handler notifications must match handler names exactly.

Ansible handler name lookup is a case-sensitive exact string match. Two
tasks notified `restart docker` while the handler in handlers/main.yml is
named `Restart docker`, so the notification resolved to no handler and
Docker was never restarted after changing /etc/docker/daemon.json or
installing nvidia-container-runtime. This test cross-checks every
`notify:` in tasks/*.yml against the handler names defined in
handlers/*.yml.
"""

from pathlib import Path

import yaml

ROLE_ROOT = Path(__file__).resolve().parent.parent


def _handler_names():
    names = set()
    for path in sorted((ROLE_ROOT / "handlers").glob("*.yml")):
        with open(path) as f:
            for task in yaml.safe_load(f) or []:
                if isinstance(task, dict) and "name" in task:
                    names.add(task["name"])
    return names


def _notifications():
    notified = []
    for path in sorted((ROLE_ROOT / "tasks").glob("*.yml")):
        with open(path) as f:
            for task in yaml.safe_load(f) or []:
                if isinstance(task, dict) and "notify" in task:
                    notify = task["notify"]
                    values = notify if isinstance(notify, list) else [notify]
                    for value in values:
                        notified.append((path.name, task.get("name"), value))
    return notified


def test_every_notify_matches_a_handler_name_case_sensitively():
    handler_names = _handler_names()
    notifications = _notifications()
    assert notifications, "expected at least one notify in tasks/*.yml"
    unresolved = [
        f"{file}: task {task_name!r} notifies {value!r}"
        for file, task_name, value in notifications
        if value not in handler_names
    ]
    assert not unresolved, (
        "notify names must exactly (case-sensitively) match a handler "
        f"name in handlers/*.yml ({sorted(handler_names)}); unresolved: "
        + "; ".join(unresolved)
    )
