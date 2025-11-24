# ==============================================================================
# file_id: SOM-SCR-0009-v1.0.0
# name: setup_tui.py
# description: Interactive TUI setup system for Privacy Proxy
# project_id: BROWSER-MIXER-ANON
# category: script
# tags: [setup, tui, installer, interactive]
# created: 2025-01-23
# modified: 2025-01-23
# version: 1.0.0
# agent_id: AGENT-PRIME-001
# execution: python setup_tui.py
# ==============================================================================

import sys
import os
import subprocess
import shutil
from pathlib import Path
import time
import platform

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.markdown import Markdown
    from rich import box
    from rich.layout import Layout
    from rich.text import Text
except ImportError:
    print("Error: 'rich' library not found.")
    print("Installing rich...")
    subprocess.run([sys.executable, "-m", "pip", "install", "rich"], check=True)
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.markdown import Markdown
    from rich import box
    from rich.text import Text

console = Console()


class PrivacyProxySetup:
    """Interactive TUI setup for Privacy Proxy"""

    def __init__(self):
        self.console = Console()
        self.base_dir = Path.cwd()
        self.venv_path = self.base_dir / ".venv"
        self.config_path = self.base_dir / "config" / "config.yaml"
        self.db_path = self.base_dir / "database" / "browser_privacy.db"
        self.logs_path = self.base_dir / "logs"
        self.is_windows = platform.system() == "Windows"

    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if self.is_windows else 'clear')

    def show_banner(self):
        """Display welcome banner"""
        self.clear_screen()
        banner = """
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║               🛡️  PRIVACY PROXY SETUP WIZARD  🛡️                    ║
    ║                                                                      ║
    ║            Browser Anonymization & Tracker Blocking Tool            ║
    ║                          Version 1.0.0                               ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
        """
        self.console.print(banner, style="bold cyan")
        self.console.print("\n[bold green]Welcome to the Privacy Proxy Interactive Setup![/bold green]\n")
        self.console.print("This wizard will guide you through the installation and configuration.\n")

        if not Confirm.ask("Ready to begin?", default=True):
            self.console.print("[yellow]Setup cancelled.[/yellow]")
            sys.exit(0)

    def check_prerequisites(self):
        """Check system prerequisites"""
        self.clear_screen()
        self.console.print(Panel.fit(
            "[bold]Step 1/7: Checking Prerequisites[/bold]",
            border_style="cyan"
        ))

        checks = []

        # Check Python version
        py_version = sys.version_info
        if py_version >= (3, 10):
            checks.append(("Python 3.10+", True, f"{py_version.major}.{py_version.minor}.{py_version.micro}"))
        else:
            checks.append(("Python 3.10+", False, f"{py_version.major}.{py_version.minor}.{py_version.micro} (too old)"))

        # Check for uv
        uv_available = shutil.which("uv") is not None
        checks.append(("uv package manager", uv_available, "Found" if uv_available else "Not found"))

        # Check for pip
        pip_available = shutil.which("pip") is not None
        checks.append(("pip", pip_available, "Found" if pip_available else "Not found"))

        # Check for git
        git_available = shutil.which("git") is not None
        checks.append(("git", git_available, "Found" if git_available else "Not found (optional)"))

        # Display results
        table = Table(title="System Check", box=box.ROUNDED)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Details", style="yellow")

        for name, passed, details in checks:
            status = "✓ Pass" if passed else "✗ Fail"
            style = "green" if passed else "red"
            table.add_row(name, f"[{style}]{status}[/{style}]", details)

        self.console.print(table)

        # Check critical requirements
        if not (py_version >= (3, 10) and (uv_available or pip_available)):
            self.console.print("\n[bold red]✗ Critical requirements not met![/bold red]")
            self.console.print("\nPlease install:")
            if py_version < (3, 10):
                self.console.print("  - Python 3.10 or higher")
            if not (uv_available or pip_available):
                self.console.print("  - pip or uv package manager")
            sys.exit(1)

        self.console.print("\n[bold green]✓ All critical checks passed![/bold green]")
        self.package_manager = "uv" if uv_available else "pip"
        input("\nPress Enter to continue...")

    def create_virtual_environment(self):
        """Create virtual environment"""
        self.clear_screen()
        self.console.print(Panel.fit(
            "[bold]Step 2/7: Creating Virtual Environment[/bold]",
            border_style="cyan"
        ))

        if self.venv_path.exists():
            self.console.print(f"[yellow]Virtual environment already exists at:[/yellow] {self.venv_path}")
            if Confirm.ask("Delete and recreate?", default=False):
                shutil.rmtree(self.venv_path)
            else:
                self.console.print("[green]Using existing virtual environment.[/green]")
                input("\nPress Enter to continue...")
                return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Creating virtual environment...", total=None)

            try:
                if self.package_manager == "uv":
                    subprocess.run(["uv", "venv", ".venv"], check=True, capture_output=True)
                else:
                    subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True, capture_output=True)

                progress.update(task, completed=True)
                self.console.print("\n[bold green]✓ Virtual environment created successfully![/bold green]")
            except subprocess.CalledProcessError as e:
                self.console.print(f"\n[bold red]✗ Failed to create virtual environment![/bold red]")
                self.console.print(f"Error: {e}")
                sys.exit(1)

        input("\nPress Enter to continue...")

    def install_dependencies(self):
        """Install Python dependencies"""
        self.clear_screen()
        self.console.print(Panel.fit(
            "[bold]Step 3/7: Installing Dependencies[/bold]",
            border_style="cyan"
        ))

        # Determine pip path
        if self.is_windows:
            pip_path = self.venv_path / "Scripts" / "pip.exe"
            python_path = self.venv_path / "Scripts" / "python.exe"
        else:
            pip_path = self.venv_path / "bin" / "pip"
            python_path = self.venv_path / "bin" / "python"

        requirements_file = self.base_dir / "requirements.txt"

        if not requirements_file.exists():
            self.console.print("[bold red]✗ requirements.txt not found![/bold red]")
            sys.exit(1)

        self.console.print(f"Installing packages from: {requirements_file}\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Installing dependencies (this may take a few minutes)...", total=None)

            try:
                if self.package_manager == "uv":
                    subprocess.run(
                        ["uv", "pip", "install", "-r", str(requirements_file)],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                else:
                    subprocess.run(
                        [str(pip_path), "install", "-r", str(requirements_file)],
                        check=True,
                        capture_output=True,
                        text=True
                    )

                progress.update(task, completed=True)
                self.console.print("\n[bold green]✓ Dependencies installed successfully![/bold green]")
            except subprocess.CalledProcessError as e:
                self.console.print(f"\n[bold red]✗ Failed to install dependencies![/bold red]")
                self.console.print(f"Error output: {e.stderr if hasattr(e, 'stderr') else str(e)}")
                sys.exit(1)

        input("\nPress Enter to continue...")

    def setup_directories(self):
        """Create necessary directories"""
        self.clear_screen()
        self.console.print(Panel.fit(
            "[bold]Step 4/7: Setting Up Directories[/bold]",
            border_style="cyan"
        ))

        directories = [
            (self.base_dir / "database", "Database storage"),
            (self.base_dir / "logs", "Log files"),
            (self.base_dir / "config", "Configuration files"),
        ]

        table = Table(title="Directory Setup", box=box.ROUNDED)
        table.add_column("Directory", style="cyan")
        table.add_column("Purpose", style="yellow")
        table.add_column("Status", style="green")

        for directory, purpose in directories:
            if directory.exists():
                status = "✓ Exists"
            else:
                directory.mkdir(parents=True, exist_ok=True)
                status = "✓ Created"
            table.add_row(str(directory.relative_to(self.base_dir)), purpose, status)

        self.console.print(table)
        self.console.print("\n[bold green]✓ All directories ready![/bold green]")
        input("\nPress Enter to continue...")

    def configure_privacy_level(self):
        """Interactive privacy level configuration"""
        self.clear_screen()
        self.console.print(Panel.fit(
            "[bold]Step 5/7: Privacy Configuration[/bold]",
            border_style="cyan"
        ))

        self.console.print("\n[bold]Select your privacy level:[/bold]\n")

        # Privacy level options
        levels = {
            "1": {
                "name": "Maximum Privacy (Paranoid)",
                "desc": "New fingerprint every request, block ALL cookies, aggressive blocking",
                "rotation_mode": "every_request",
                "block_all": True,
                "auto_block": True,
                "threshold": 1
            },
            "2": {
                "name": "Balanced Privacy (Recommended)",
                "desc": "Rotate every 5 minutes, block cookies, moderate blocking",
                "rotation_mode": "interval",
                "block_all": True,
                "auto_block": True,
                "threshold": 3
            },
            "3": {
                "name": "Minimal Privacy (Testing)",
                "desc": "Rotate on launch, log cookies but don't block, no auto-blocking",
                "rotation_mode": "launch",
                "block_all": False,
                "auto_block": False,
                "threshold": 10
            },
            "4": {
                "name": "Custom Configuration",
                "desc": "Configure settings manually",
                "rotation_mode": None,
                "block_all": None,
                "auto_block": None,
                "threshold": None
            }
        }

        table = Table(box=box.ROUNDED)
        table.add_column("Option", style="cyan", justify="center")
        table.add_column("Privacy Level", style="bold magenta")
        table.add_column("Description", style="yellow")

        for key, level in levels.items():
            table.add_row(key, level["name"], level["desc"])

        self.console.print(table)

        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4"], default="2")

        selected = levels[choice]

        if choice == "4":
            # Custom configuration
            self.console.print("\n[bold]Custom Configuration:[/bold]\n")

            rotation_mode = Prompt.ask(
                "Fingerprint rotation mode",
                choices=["every_request", "interval", "new_tab", "launch"],
                default="interval"
            )

            block_all = Confirm.ask("Block ALL cookies?", default=True)
            auto_block = Confirm.ask("Enable auto-blocking?", default=True)

            if auto_block:
                threshold = int(Prompt.ask("Auto-block threshold (hits)", default="3"))
            else:
                threshold = 999

            config_values = {
                "rotation_mode": rotation_mode,
                "block_all": block_all,
                "auto_block": auto_block,
                "threshold": threshold
            }
        else:
            config_values = selected

        # Save configuration
        self.save_configuration(config_values)

        self.console.print(f"\n[bold green]✓ Configuration saved:[/bold green] {selected['name']}")
        input("\nPress Enter to continue...")

    def save_configuration(self, values):
        """Save configuration to YAML file"""
        import yaml

        config = {
            "proxy": {
                "host": "127.0.0.1",
                "port": 8080,
                "https_port": 8081
            },
            "fingerprint": {
                "rotation_mode": values["rotation_mode"] or "every_request",
                "rotation_interval": 300,
                "randomize_user_agent": True,
                "randomize_accept_language": True,
                "randomize_accept_encoding": True,
                "randomize_platform": True,
                "strip_referer": True,
                "randomize_dnt": True,
                "strip_headers": [
                    "X-Forwarded-For",
                    "X-Real-IP",
                    "Via",
                    "X-Client-IP"
                ]
            },
            "cookies": {
                "block_all": values["block_all"] if values["block_all"] is not None else True,
                "log_attempts": True,
                "auto_block_trackers": True
            },
            "blocking": {
                "auto_block": values["auto_block"] if values["auto_block"] is not None else True,
                "auto_block_threshold": values["threshold"] or 3,
                "use_builtin_lists": True,
                "block_patterns": [
                    ".*analytics.*",
                    ".*doubleclick.*",
                    ".*facebook.*",
                    ".*google-analytics.*",
                    ".*googletagmanager.*",
                    ".*scorecardresearch.*",
                    ".*adservice.*",
                    ".*adsystem.*",
                    ".*advertising.*"
                ]
            },
            "database": {
                "path": "database/browser_privacy.db",
                "log_requests": True,
                "log_cookies": True,
                "log_fingerprints": True
            },
            "logging": {
                "level": "INFO",
                "file": "logs/privacy_proxy.log",
                "console": True
            },
            "whitelist": [
                "localhost",
                "127.0.0.1"
            ]
        }

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def initialize_database(self):
        """Initialize SQLite database"""
        self.clear_screen()
        self.console.print(Panel.fit(
            "[bold]Step 6/7: Initializing Database[/bold]",
            border_style="cyan"
        ))

        if self.db_path.exists():
            self.console.print(f"[yellow]Database already exists:[/yellow] {self.db_path}")
            if not Confirm.ask("Keep existing database?", default=True):
                self.db_path.unlink()
                self.console.print("[yellow]Deleted existing database.[/yellow]")
            else:
                self.console.print("[green]Using existing database.[/green]")
                input("\nPress Enter to continue...")
                return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Initializing database...", total=None)

            try:
                # Initialize database using database_handler
                sys.path.insert(0, str(self.base_dir))
                from database_handler import DatabaseHandler

                db = DatabaseHandler(str(self.db_path))
                db.add_diary_entry(
                    "setup",
                    "Initial Setup",
                    "Database initialized via TUI setup wizard"
                )
                db.close()

                progress.update(task, completed=True)
                self.console.print("\n[bold green]✓ Database initialized successfully![/bold green]")
                self.console.print(f"Location: {self.db_path}")
            except Exception as e:
                self.console.print(f"\n[bold red]✗ Failed to initialize database![/bold red]")
                self.console.print(f"Error: {e}")
                sys.exit(1)

        input("\nPress Enter to continue...")

    def run_verification(self):
        """Verify installation"""
        self.clear_screen()
        self.console.print(Panel.fit(
            "[bold]Step 7/7: Verification[/bold]",
            border_style="cyan"
        ))

        checks = []

        # Check venv
        checks.append(("Virtual Environment", self.venv_path.exists(), str(self.venv_path)))

        # Check config
        checks.append(("Configuration File", self.config_path.exists(), str(self.config_path)))

        # Check database
        checks.append(("Database File", self.db_path.exists(), str(self.db_path)))

        # Check main files
        checks.append(("privacy_proxy.py", (self.base_dir / "privacy_proxy.py").exists(), "Main proxy module"))
        checks.append(("start_proxy.py", (self.base_dir / "start_proxy.py").exists(), "Launcher script"))
        checks.append(("manage.py", (self.base_dir / "manage.py").exists(), "Management CLI"))

        # Display results
        table = Table(title="Installation Verification", box=box.ROUNDED)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Details", style="yellow")

        all_passed = True
        for name, passed, details in checks:
            status = "✓ OK" if passed else "✗ Missing"
            style = "green" if passed else "red"
            table.add_row(name, f"[{style}]{status}[/{style}]", details)
            if not passed:
                all_passed = False

        self.console.print(table)

        if all_passed:
            self.console.print("\n[bold green]✓ All components verified successfully![/bold green]")
        else:
            self.console.print("\n[bold yellow]⚠ Some components are missing. Setup may be incomplete.[/bold yellow]")

        input("\nPress Enter to continue...")

    def show_completion(self):
        """Show completion message and next steps"""
        self.clear_screen()

        completion_text = """
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║                    ✓ SETUP COMPLETE! ✓                              ║
    ║                                                                      ║
    ║              Privacy Proxy is ready to use!                          ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
        """

        self.console.print(completion_text, style="bold green")

        # Next steps
        next_steps = """
## 🚀 Next Steps

### 1. Start the Proxy
"""

        if self.is_windows:
            next_steps += """
```powershell
.venv\\Scripts\\activate.ps1
python start_proxy.py
```
"""
        else:
            next_steps += """
```bash
source .venv/bin/activate
python start_proxy.py
```
"""

        next_steps += """
### 2. Configure Your Browser

**Firefox:**
- Settings → Network Settings → Manual proxy configuration
- HTTP Proxy: `127.0.0.1`, Port: `8080`
- HTTPS Proxy: `127.0.0.1`, Port: `8080`

**Chrome/Edge:**
- Settings → System → Open proxy settings
- Address: `127.0.0.1`, Port: `8080`

### 3. Install HTTPS Certificate

- Visit: `http://mitm.it`
- Download and install certificate for your OS
- Restart browser

### 4. Management Commands

View statistics:
```bash
python manage.py stats
```

List blocked domains:
```bash
python manage.py domains --limit 50
```

Export blocklist:
```bash
python manage.py export blocklist.txt --format hosts
```

---

📖 **Full Documentation:** README.md
🏗️ **Architecture:** ARCHITECTURE.md
⚡ **Quick Start:** QUICKSTART.md

Happy private browsing! 🛡️
        """

        self.console.print(Markdown(next_steps))

        self.console.print("\n" + "="*70)
        self.console.print("[bold cyan]Thank you for using Privacy Proxy![/bold cyan]")
        self.console.print("="*70 + "\n")

    def run(self):
        """Run the complete setup wizard"""
        try:
            self.show_banner()
            self.check_prerequisites()
            self.create_virtual_environment()
            self.install_dependencies()
            self.setup_directories()
            self.configure_privacy_level()
            self.initialize_database()
            self.run_verification()
            self.show_completion()
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Setup interrupted by user.[/yellow]")
            sys.exit(1)
        except Exception as e:
            self.console.print(f"\n\n[bold red]Unexpected error:[/bold red] {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point"""
    setup = PrivacyProxySetup()
    setup.run()


if __name__ == "__main__":
    main()
