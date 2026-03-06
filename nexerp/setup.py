import frappe
import json
import os


MODULE_SIDEBAR_ICON = {
    "Accounts": "dollar-sign",
    "Buying": "shopping-cart",
    "Selling": "tag",
    "Stock": "package",
    "Manufacturing": "tool",
    "Assets": "box",
    "Projects": "clipboard",
    "CRM": "target",
    "Support": "headphones",
    "HR and Payroll": "user",
    "Payroll": "credit-card",
    "Quality Management": "check-circle",
    "Loan Management": "credit-card",
    "KSA Compliance": "shield",
    "Healthcare": "activity",
    "Education": "book",
    "Communication": "message-circle",
    "Setup": "settings",
    "Integrations": "link",
    "Website": "globe",
    "Workflow": "git-merge",
}


SKIP_MODULES = {
    "Frappe",
    "Core",
    "Custom",
    "Desk",
    "Email",
    "Event Streaming",
    "File",
    "Monitor",
    "Rate Limiting",
    "Social",
    "Test Runner",
    "Translate",
    "Twilio",
    "Zoom",
    "Data Import Tool",
    "Bulk Transaction",
    "Automation",
    "ChatGPT",
    "Geo",
}


def sync_nexerp_fixtures():
    """Create / update NexERP Dashboard, Workspace and Workspace Sidebar."""
    _sync_fixture_file("Dashboard", "dashboard.json")
    _generate_workspace_and_sidebar()


def _sync_fixture_file(doctype, filename):
    """Import a single fixture JSON file, bypassing link validation."""
    path = os.path.join(frappe.get_app_path("nexerp"), "fixtures", filename)
    if not os.path.exists(path):
        return
    with open(path) as fh:
        records = json.load(fh)
    for rec in records:
        name = rec.get("name")
        if not name:
            continue
        try:
            if frappe.db.exists(doctype, name):
                doc = frappe.get_doc(doctype, name)
                doc.update(rec)
            else:
                doc = frappe.get_doc(rec)
            _set_ignore_flags(doc)
            if doc.is_new():
                doc.insert(ignore_permissions=True, ignore_links=True)
            else:
                doc.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception as exc:
            frappe.db.rollback()
            frappe.logger().error(f"NexERP fixture sync [{doctype}][{name}]: {exc}")


def _set_ignore_flags(doc):
    doc.flags.ignore_permissions = True
    doc.flags.ignore_links = True
    doc.flags.ignore_validate = False
    doc.flags.in_migrate = True


def _generate_workspace_and_sidebar():
    """
    Query ALL doctypes & reports from ERPNext, HRMS and any KSA-Compliance
    modules and build a single NexERP Workspace + Workspace Sidebar.
    """
    installed = frappe.get_installed_apps()

    app_order = []
    for app in ("ksa_compliance", "erpnext", "hrms", "nexerp"):
        if app in installed:
            app_order.append(app)

    module_data = []

    for app in app_order:
        modules = frappe.get_all(
            "Module Def",
            filters={"app_name": app},
            pluck="name",
            order_by="name",
        )
        for mod in modules:
            if mod in SKIP_MODULES:
                continue

            dts = _get_doctypes(mod)
            rps = _get_reports(mod)

            if dts or rps:
                module_data.append({"module": mod, "doctypes": dts, "reports": rps})

    if not module_data:
        frappe.logger().warning(
            "NexERP: no module data found – skipping workspace build"
        )
        return

    content_blocks, workspace_links, sidebar_items = _build_data(module_data)

    _upsert_workspace(content_blocks, workspace_links)
    _upsert_sidebar(sidebar_items)


def _get_doctypes(module):
    return frappe.get_all(
        "DocType",
        filters=[
            ["module", "=", module],
            ["istable", "=", 0],
            ["is_virtual", "=", 0],
        ],
        pluck="name",
        order_by="name",
    )


def _get_reports(module):
    return frappe.get_all(
        "Report",
        filters={"module": module, "disabled": 0},
        pluck="name",
        order_by="name",
    )


def _build_data(module_data):
    """Return (content_blocks, workspace_links, sidebar_items) for all modules."""
    content_blocks = []
    workspace_links = []
    sidebar_items = []

    sidebar_items += [
        _make_sidebar_link("Home", "NexERP", "Workspace", "home", idx=1),
        _make_sidebar_link(
            "Dashboard", "NexERP Dashboard", "Dashboard", "bar-chart-2", idx=2
        ),
    ]

    block_n = 1
    item_idx = 3

    for mod_info in module_data:
        mod = mod_info["module"]
        dts = mod_info["doctypes"]
        rps = mod_info["reports"]
        s_icon = MODULE_SIDEBAR_ICON.get(mod, "layers")
        safe = frappe.scrub(mod)

        content_blocks.append(
            {
                "id": f"c_{safe}_{block_n}",
                "type": "card",
                "data": {"card_name": mod, "col": 4},
            }
        )

        workspace_links.append(_wl_card_break(mod, len(dts) + len(rps)))

        for dt in dts:
            workspace_links.append(_wl_link(dt, dt, "DocType", is_query=0))
        for rp in rps:
            workspace_links.append(_wl_link(rp, rp, "Report", is_query=1))

        sidebar_items.append(
            {
                "child": 0,
                "collapsible": 1,
                "display_depends_on": None,
                "filters": None,
                "icon": s_icon,
                "indent": 1,
                "keep_closed": 1,
                "label": mod,
                "link_to": None,
                "link_type": None,
                "navigate_to_tab": None,
                "route_options": None,
                "show_arrow": 1,
                "type": "Section Break",
                "url": None,
                "idx": item_idx,
            }
        )
        item_idx += 1

        for dt in dts:
            sidebar_items.append(
                _make_sidebar_link(dt, dt, "DocType", "list", idx=item_idx, child=1)
            )
            item_idx += 1

        for rp in rps:
            sidebar_items.append(
                _make_sidebar_link(rp, rp, "Report", "table", idx=item_idx, child=1)
            )
            item_idx += 1

        block_n += 1

    return content_blocks, workspace_links, sidebar_items


def _make_sidebar_link(label, link_to, link_type, icon, idx, child=0):
    return {
        "child": child,
        "collapsible": 0,
        "display_depends_on": None,
        "filters": None,
        "icon": icon,
        "indent": 0,
        "keep_closed": 0,
        "label": label,
        "link_to": link_to,
        "link_type": link_type,
        "navigate_to_tab": None,
        "route_options": None,
        "show_arrow": 0,
        "type": "Link",
        "url": None,
        "idx": idx,
    }


def _wl_card_break(label, link_count):
    return {
        "type": "Card Break",
        "label": label,
        "link_count": link_count,
        "link_to": None,
        "link_type": None,
        "is_query_report": 0,
        "hidden": 0,
        "onboard": 0,
        "dependencies": None,
        "description": None,
        "icon": None,
        "only_for": None,
        "report_ref_doctype": None,
    }


def _wl_link(label, link_to, link_type, is_query):
    return {
        "type": "Link",
        "label": label,
        "link_to": link_to,
        "link_type": link_type,
        "is_query_report": is_query,
        "hidden": 0,
        "onboard": 0,
        "dependencies": None,
        "description": None,
        "icon": None,
        "only_for": None,
        "report_ref_doctype": None,
    }


def _upsert_workspace(content_blocks, links):
    name = "NexERP"
    try:
        if frappe.db.exists("Workspace", name):
            doc = frappe.get_doc("Workspace", name)
        else:
            doc = frappe.new_doc("Workspace")
            doc.name = name

        doc.label = name
        doc.title = name
        doc.app = "nexerp"
        doc.icon = "grid"
        doc.is_hidden = 0
        doc.content = json.dumps(content_blocks)
        doc.links = []
        for lk in links:
            doc.append("links", lk)

        _set_ignore_flags(doc)
        if doc.is_new():
            doc.insert(ignore_permissions=True, ignore_links=True)
        else:
            doc.save(ignore_permissions=True)

        frappe.db.commit()
        frappe.logger().info(
            f"NexERP: Workspace '{name}' saved – {len(links)} link rows"
        )
    except Exception as exc:
        frappe.db.rollback()
        frappe.logger().error(f"NexERP: Workspace upsert failed: {exc}")
        raise


def _upsert_sidebar(items):
    name = "NexERP"
    try:
        if frappe.db.exists("Workspace Sidebar", name):
            doc = frappe.get_doc("Workspace Sidebar", name)
        else:
            doc = frappe.new_doc("Workspace Sidebar")
            doc.name = name

        doc.title = name
        doc.app = "nexerp"
        doc.header_icon = "grid"
        doc.standard = 1
        doc.items = []
        for it in items:
            doc.append("items", it)

        _set_ignore_flags(doc)
        if doc.is_new():
            doc.insert(ignore_permissions=True, ignore_links=True)
        else:
            doc.save(ignore_permissions=True)

        frappe.db.commit()
        frappe.logger().info(
            f"NexERP: Workspace Sidebar '{name}' saved – {len(items)} items"
        )
    except Exception as exc:
        frappe.db.rollback()
        frappe.logger().error(f"NexERP: Workspace Sidebar upsert failed: {exc}")
        raise
