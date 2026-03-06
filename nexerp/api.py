import frappe
import json
import os


def override_sidebar_data(bootinfo):

    sidebar_json_path = os.path.join(
        frappe.get_app_path("nexerp"), "workspace_sidebar", "nexerp.json"
    )

    if not os.path.exists(sidebar_json_path):
        return

    with open(sidebar_json_path, "r") as f:
        sidebar_data = json.load(f)

    sidebar_key = sidebar_data.get("name", "NexERP").lower()

    bootinfo.workspace_sidebar_item[sidebar_key] = frappe._dict(
        {
            "label": sidebar_data.get("title", "NexERP"),
            "header_icon": sidebar_data.get("header_icon", "grid"),
            "module_onboarding": None,
            "module": None,
            "app": "nexerp",
            "items": [frappe._dict(item) for item in sidebar_data.get("items", [])],
        }
    )

    if "my workspaces" not in bootinfo.workspace_sidebar_item:
        bootinfo.workspace_sidebar_item["my workspaces"] = frappe._dict(
            {
                "label": "My Workspaces",
                "header_icon": "user-round",
                "module_onboarding": None,
                "module": None,
                "app": "frappe",
                "items": [],
            }
        )
