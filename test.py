from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Input, ListView, ListItem, Label
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding

class Sidebar(Static):
    def compose(self) -> ComposeResult:
        yield ListView(
            ListItem(Label("Dashboard"), id="dashboard"),
            ListItem(Label("Settings"), id="settings"),
            ListItem(Label("About"), id="about"),
        )

class Dashboard(Static):
    def compose(self) -> ComposeResult:
        yield Label("Welcome to the Manus Textual TUI Demo!", classes="title")
        yield Horizontal(
            Vertical(
                Label("System Status: OK", classes="status"),
                Label("Uptime: 1h 23m"),
                Label("Memory Usage: 42%"),
                classes="card"
            ),
            Vertical(
                Label("Active Tasks: 5"),
                Label("Completed Tasks: 12"),
                Label("Pending Notifications: 3"),
                classes="card"
            ),
        )
        yield Button("Refresh Data", variant="primary", id="refresh_btn")

class Settings(Static):
    def compose(self) -> ComposeResult:
        yield Label("Application Settings", classes="title")
        yield Horizontal(
            Label("Username: "),
            Input(placeholder="Enter username..."),
        )
        yield Horizontal(
            Label("Dark Mode: "),
            Button("Toggle", variant="default"),
        )

class About(Static):
    def compose(self) -> ComposeResult:
        yield Label("About This TUI", classes="title")
        yield Label("This is a demonstration of the Textual library for Python.")
        yield Label("Built with love by Manus.")

class TUIDemoApp(App):
    CSS = """
    Screen {
        background: $surface;
    }

    #sidebar {
        width: 25;
        background: $panel;
        border-right: tall $primary;
    }

    .title {
        font-size: 150%;
        text-style: bold;
        margin: 1 0;
        color: $accent;
    }

    .card {
        border: solid $primary;
        padding: 1;
        margin: 1;
        height: auto;
    }

    .status {
        color: green;
        text-style: bold;
    }

    Horizontal {
        height: auto;
    }

    Vertical {
        width: 1fr;
    }

    #main_content {
        padding: 1 2;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit App"),
        Binding("d", "switch_to('dashboard')", "Dashboard"),
        Binding("s", "switch_to('settings')", "Settings"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Sidebar(id="sidebar"),
            Container(Dashboard(id="dashboard_view"), id="main_content"),
        )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        content = self.query_one("#main_content")
        for child in content.children:
            child.remove()
        
        selected_id = event.item.id
        if selected_id == "dashboard":
            content.mount(Dashboard())
        elif selected_id == "settings":
            content.mount(Settings())
        elif selected_id == "about":
            content.mount(About())

    def action_switch_to(self, view_id: str) -> None:
        content = self.query_one("#main_content")
        for child in content.children:
            child.remove()
        
        if view_id == "dashboard":
            content.mount(Dashboard())
        elif view_id == "settings":
            content.mount(Settings())
        elif view_id == "about":
            content.mount(About())

if __name__ == "__main__":
    app = TUIDemoApp()
    app.run()
