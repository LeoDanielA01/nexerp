$(document).on('app_ready', function () {
    var LOCKED_SIDEBAR = "NexERP";
    var HOME_WORKSPACE = "nexerp";
    if (!frappe.ui || !frappe.ui.Sidebar) return;
    var isAdmin = (
        frappe.session.user === "Administrator" ||
        frappe.user.has_role("Administrator")
    );
    if (!isAdmin) {
        $("<style id='nexerp-nav-restrict'>")
            .text(
                ".standard-actions a[href='/desk']," +
                ".standard-actions a[href='/']," +
                ".navbar-home," +
                ".sidebar-item-desktop," +
                ".sidebar-item-website { display: none !important; }"
            )
            .appendTo("head");

        function hideByText() {
            $("a.dropdown-item").each(function () {
                var txt = $(this).text().trim();
                if (txt === "Desktop" || txt === "Website") {
                    $(this).hide();
                }
            });
        }
        $(document).on("page-change", hideByText);
        $(document).on("click show.bs.dropdown", function () {
            setTimeout(hideByText, 50);
        });
        hideByText();
    }
    function redirectIfOnAppsPage() {
        try {
            var route = frappe.get_route && frappe.get_route();
            if (!route || route.length === 0 || route[0] === "") {
                frappe.set_route("dashboard-view", "NexERP Dashboard");
            }
        } catch (e) {}
    }
    $(document).on("page-change", redirectIfOnAppsPage);
    setTimeout(redirectIfOnAppsPage, 200);
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
