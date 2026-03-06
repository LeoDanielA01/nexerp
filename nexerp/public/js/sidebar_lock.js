$(document).on('app_ready', function () {

    var LOCKED_SIDEBAR = "NexERP";

    if (!frappe.ui || !frappe.ui.Sidebar) return;

    var _origSetup = frappe.ui.Sidebar.prototype.setup;
    frappe.ui.Sidebar.prototype.setup = function (title) {
        return _origSetup.call(this, LOCKED_SIDEBAR);
    };

    frappe.ui.Sidebar.prototype.set_workspace_sidebar = function () {
        if (this.sidebar_title !== LOCKED_SIDEBAR) {
            _origSetup.call(this, LOCKED_SIDEBAR);
        } else {
            this.set_active_workspace_item && this.set_active_workspace_item();
        }
    };
    
    frappe.ui.Sidebar.prototype.set_sidebar_for_page = function () {};
    frappe.ui.Sidebar.prototype.show_sidebar_for_module = function () {};
});
