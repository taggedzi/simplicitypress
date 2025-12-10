from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
import shutil
import subprocess
import sys
import webbrowser

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtGui import QCloseEvent, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)


@dataclass
class CommandSpec:
    """
    Description of a command to run via subprocess.
    """

    args: list[str]
    cwd: Optional[Path] = None


class CommandWorker(QObject):
    """
    Run a subprocess command in a background thread and emit progress.
    """

    progress = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, spec: CommandSpec) -> None:
        super().__init__()
        self._spec = spec

    def run(self) -> None:
        """
        Run the configured command, emitting progress and finished signals.
        """
        cmd_display = " ".join(self._spec.args)
        self.progress.emit(f"$ {cmd_display}")
        try:
            process = subprocess.Popen(
                self._spec.args,
                cwd=str(self._spec.cwd) if self._spec.cwd is not None else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except Exception as exc:  # noqa: BLE001
            self.progress.emit(f"Failed to start command: {exc}")
            self.finished.emit(False, "Failed to start command")
            return

        assert process.stdout is not None
        for line in process.stdout:
            self.progress.emit(line.rstrip("\n"))

        process.wait()
        success = process.returncode == 0
        if success:
            message = "Command completed successfully."
        else:
            message = f"Command failed with exit code {process.returncode}."
        self.finished.emit(success, message)


def is_simplicitypress_site(site_root: Path) -> bool:
    """
    Return True if the given directory looks like a SimplicityPress site.
    """
    return (site_root / "site.toml").is_file()


def default_output_dir(site_root: Path) -> Path:
    """
    Return the default output directory for the given site root.
    """
    return site_root / "output"


class SimplicityPressWindow(QMainWindow):
    """
    Main window for the SimplicityPress GUI.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SimplicityPress")
        self._current_thread: Optional[QThread] = None
        self._current_worker: Optional[CommandWorker] = None
        self._command_running = False
        self._serve_process: Optional[subprocess.Popen] = None
        self._serve_port: int = 8000

        self._build_ui()
        self._update_site_state()

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        # Site root selection
        site_root_layout = QGridLayout()
        site_root_label = QLabel("Site root:")
        self.site_root_edit = QLineEdit()
        self.site_root_browse_button = QPushButton("Browse…")
        self.site_root_browse_button.clicked.connect(self._browse_site_root)

        site_root_layout.addWidget(site_root_label, 0, 0)
        site_root_layout.addWidget(self.site_root_edit, 0, 1)
        site_root_layout.addWidget(self.site_root_browse_button, 0, 2)

        # Output directory selection
        output_label = QLabel("Output directory:")
        self.output_edit = QLineEdit()
        self.output_browse_button = QPushButton("Browse…")
        self.output_reset_button = QPushButton("Reset to default")
        self.output_browse_button.clicked.connect(self._browse_output_dir)
        self.output_reset_button.clicked.connect(self._reset_output_dir)

        output_layout = QGridLayout()
        output_layout.addWidget(output_label, 0, 0)
        output_layout.addWidget(self.output_edit, 0, 1)
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.output_browse_button)
        buttons_layout.addWidget(self.output_reset_button)
        output_layout.addLayout(buttons_layout, 0, 2)

        # Build options
        options_layout = QHBoxLayout()
        self.include_drafts_checkbox = QCheckBox("Include drafts")
        self.clear_output_checkbox = QCheckBox("Clear output before build (dangerous!)")
        options_layout.addWidget(self.include_drafts_checkbox)
        options_layout.addWidget(self.clear_output_checkbox)
        options_layout.addStretch(1)

        # Action buttons
        actions_layout = QHBoxLayout()
        self.init_button = QPushButton("Initialize site here")
        self.build_button = QPushButton("Build site")
        self.preview_button = QPushButton("Preview output")

        self.init_button.clicked.connect(self._on_init_clicked)
        self.build_button.clicked.connect(self._on_build_clicked)
        self.preview_button.clicked.connect(self._on_preview_clicked)

        actions_layout.addWidget(self.init_button)
        actions_layout.addWidget(self.build_button)
        actions_layout.addWidget(self.preview_button)
        actions_layout.addStretch(1)

        # Status and progress
        self.status_label = QLabel("Select a site root to get started.")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)

        # Log window
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        main_layout.addLayout(site_root_layout)
        main_layout.addLayout(output_layout)
        main_layout.addLayout(options_layout)
        main_layout.addLayout(actions_layout)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.log_edit)

        # Connect edits
        self.site_root_edit.editingFinished.connect(self._on_site_root_changed)
        self.output_edit.editingFinished.connect(self._on_output_changed)

    def _on_site_root_changed(self) -> None:
        self._update_site_state()

    def _on_output_changed(self) -> None:
        # Nothing dynamic for now; placeholder to keep behavior explicit.
        pass

    def _browse_site_root(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select site root")
        if directory:
            self.site_root_edit.setText(directory)
            self._update_site_state()

    def _browse_output_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select output directory")
        if directory:
            self.output_edit.setText(directory)

    def _reset_output_dir(self) -> None:
        root = self._current_site_root()
        if root is None:
            return
        default_dir = default_output_dir(root)
        self.output_edit.setText(str(default_dir))

    def _current_site_root(self) -> Optional[Path]:
        text = self.site_root_edit.text().strip()
        if not text:
            return None
        path = Path(text).expanduser()
        if not path.exists() or not path.is_dir():
            return None
        return path

    def _current_output_dir(self, site_root: Path) -> Path:
        text = self.output_edit.text().strip()
        if text:
            return Path(text).expanduser()
        return default_output_dir(site_root)

    def _update_site_state(self) -> None:
        root = self._current_site_root()
        if root is None:
            self.status_label.setText("Select a site root to get started.")
            self.init_button.setEnabled(False)
            self.build_button.setEnabled(False)
            self.preview_button.setEnabled(False)
            return

        if is_simplicitypress_site(root):
            self.status_label.setText("SimplicityPress site detected.")
            self.init_button.setEnabled(False)
            self.build_button.setEnabled(True)
            self.preview_button.setEnabled(True)
        else:
            self.status_label.setText(
                "No site.toml found. You can initialize a new site here.",
            )
            self.init_button.setEnabled(True)
            self.build_button.setEnabled(False)
            self.preview_button.setEnabled(False)

        # Set default output directory if empty.
        if not self.output_edit.text().strip():
            self.output_edit.setText(str(default_output_dir(root)))

    def _append_log(self, text: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_edit.append(f"[{timestamp}] {text}")
        self.log_edit.moveCursor(QTextCursor.End)

    def _set_busy(self, busy: bool) -> None:
        self._command_running = busy
        if busy:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.progress_bar.setRange(0, 0)
        else:
            QApplication.restoreOverrideCursor()
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(0)

        # Enable/disable controls
        enabled = not busy
        self.site_root_edit.setEnabled(enabled)
        self.site_root_browse_button.setEnabled(enabled)
        self.output_edit.setEnabled(enabled)
        self.output_browse_button.setEnabled(enabled)
        self.output_reset_button.setEnabled(enabled)
        self.include_drafts_checkbox.setEnabled(enabled)
        self.clear_output_checkbox.setEnabled(enabled)
        self.init_button.setEnabled(enabled and self.init_button.isEnabled())
        self.build_button.setEnabled(enabled and self.build_button.isEnabled())
        self.preview_button.setEnabled(enabled and self.preview_button.isEnabled())

    def _start_command(self, spec: CommandSpec, status_message: str) -> None:
        if self._command_running:
            QMessageBox.information(self, "Busy", "A command is already running.")
            return

        self.status_label.setText(status_message)
        self._append_log(status_message)
        self._set_busy(True)

        thread = QThread(self)
        worker = CommandWorker(spec)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.progress.connect(self._append_log)
        worker.finished.connect(self._on_command_finished)
        worker.finished.connect(lambda *_: thread.quit())
        worker.finished.connect(lambda *_: worker.deleteLater())
        thread.finished.connect(thread.deleteLater)

        self._current_thread = thread
        self._current_worker = worker

        def _cleanup() -> None:
            self._current_thread = None
            self._current_worker = None

        thread.finished.connect(_cleanup)
        thread.start()

    def _on_command_finished(self, success: bool, message: str) -> None:
        self._set_busy(False)
        self.status_label.setText(message)
        self._append_log(message)
        # Re-evaluate site state after command (e.g. after init).
        self._update_site_state()

    def _on_init_clicked(self) -> None:
        root = self._current_site_root()
        if root is None:
            QMessageBox.warning(self, "Invalid site root", "Please select a valid directory.")
            return

        spec = CommandSpec(
            args=[sys.executable, "-m", "simplicitypress", "init", "--site-root", str(root)],
            cwd=root,
        )
        self._start_command(spec, "Initializing site...")

    def _on_build_clicked(self) -> None:
        root = self._current_site_root()
        if root is None or not is_simplicitypress_site(root):
            QMessageBox.warning(self, "Invalid site root", "Please select a SimplicityPress site.")
            return

        output_dir = self._current_output_dir(root)

        # Handle clear output option.
        if self.clear_output_checkbox.isChecked() and output_dir.exists():
            try:
                has_contents = any(output_dir.iterdir())
            except OSError:
                has_contents = True
            if has_contents:
                reply = QMessageBox.warning(
                    self,
                    "Clear output directory",
                    f"This will delete everything under:\n{output_dir}\n\nAre you sure?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    return
                try:
                    shutil.rmtree(output_dir)
                except Exception as exc:  # noqa: BLE001
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to clear output directory:\n{exc}",
                    )
                    return

        args: list[str] = [sys.executable, "-m", "simplicitypress", "build", "--site-root", str(root)]
        if output_dir:
            args.extend(["--output", str(output_dir)])
        if self.include_drafts_checkbox.isChecked():
            args.append("--include-drafts")

        spec = CommandSpec(args=args, cwd=root)
        self._start_command(spec, "Building site...")

    def _on_preview_clicked(self) -> None:
        # If a preview server is already running, offer to stop it.
        if self._serve_process is not None and self._serve_process.poll() is None:
            reply = QMessageBox.question(
                self,
                "Stop preview server",
                "A preview server is currently running.\n\nStop preview server?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                try:
                    self._serve_process.terminate()
                    self._serve_process.wait(timeout=5)
                except Exception:
                    # Best-effort shutdown; ignore errors.
                    pass
                finally:
                    self._serve_process = None
                self.status_label.setText("Preview server stopped.")
                self._append_log("Preview server stopped.")
            return

        root = self._current_site_root()
        if root is None or not is_simplicitypress_site(root):
            QMessageBox.warning(
                self,
                "Invalid site root",
                "Please select a SimplicityPress site.",
            )
            return

        output_dir = self._current_output_dir(root)

        args: list[str] = [
            sys.executable,
            "-m",
            "simplicitypress",
            "serve",
            "--site-root",
            str(root),
            "--port",
            str(self._serve_port),
        ]
        if output_dir:
            args.extend(
                [
                    "--output",
                    str(output_dir),
                    "--no-build",
                ],
            )

        try:
            self._append_log(f"Starting preview server: {' '.join(args)}")
            process = subprocess.Popen(args, cwd=root)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to start preview server:\n{exc}",
            )
            self._append_log(f"Failed to start preview server: {exc}")
            return

        self._serve_process = process
        url = f"http://127.0.0.1:{self._serve_port}/"
        self.status_label.setText(f"Preview server running at {url}")
        self._append_log(f"Preview server running at {url}")

        try:
            webbrowser.open(url)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open browser:\n{exc}",
            )
            self._append_log(f"Failed to open browser: {exc}")

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        # Ensure background thread is stopped on close.
        thread = self._current_thread
        if thread is not None:
            try:
                if thread.isRunning():
                    thread.quit()
                    thread.wait(2000)
            except RuntimeError:
                # Underlying C++ thread object may already be deleted.
                pass

        # Ensure preview server process is stopped on close.
        if self._serve_process is not None and self._serve_process.poll() is None:
            try:
                self._serve_process.terminate()
                self._serve_process.wait(timeout=5)
            except Exception:
                pass
            finally:
                self._serve_process = None

        event.accept()


def main() -> None:
    """
    Entry point for launching the SimplicityPress GUI.
    """
    app = QApplication(sys.argv)
    window = SimplicityPressWindow()
    window.resize(900, 700)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
