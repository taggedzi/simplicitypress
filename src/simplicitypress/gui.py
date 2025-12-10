from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
from collections.abc import Callable
import shutil
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

from .api import build_site_api, init_site
from .core import ProgressEvent


@dataclass
class TaskSpec:
    """
    Description of a background task to run in a worker thread.
    """

    label: str
    func: Callable[..., Any]
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.kwargs is None:
            self.kwargs = {}


class CommandWorker(QObject):
    """
    Run a subprocess command in a background thread and emit progress.
    """

    progress = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, spec: TaskSpec) -> None:
        super().__init__()
        self._spec = spec

    def run(self) -> None:
        """
        Run the configured task, emitting progress and finished signals.
        """
        self.progress.emit(f"$ {self._spec.label}")
        try:
            self._spec.func(*self._spec.args, **self._spec.kwargs)  # type: ignore[arg-type]
        except Exception as exc:  # noqa: BLE001
            self.progress.emit(f"[ERROR] {exc!r}")
            self.finished.emit(False, "Task failed. See log.")
            return
        self.finished.emit(True, "Task completed.")


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
        self.log_edit.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding,
        )

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
        self.log_edit.moveCursor(QTextCursor.MoveOperation.End)

    def _log_progress_event(self, event: ProgressEvent) -> None:
        """
        Append a log line derived from a ProgressEvent.
        """
        message = event.message or ""
        self._append_log(f"[{event.stage.value}] {message}")

    def _set_busy(self, busy: bool) -> None:
        self._command_running = busy
        if busy:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
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

    def _start_task(self, spec: TaskSpec, status_message: str) -> None:
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
            QMessageBox.warning(self, "No site root", "Select a site root first.")
            return

        spec = TaskSpec(
            label=f"init --site-root {root}",
            func=init_site,
            args=(root,),
        )
        self._start_task(spec, "Initializing site...")

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
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
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

        include_drafts = self.include_drafts_checkbox.isChecked()

        spec = TaskSpec(
            label=f"build --site-root {root}",
            func=build_site_api,
            args=(root,),
            kwargs={
                "output_dir": output_dir,
                "include_drafts": include_drafts,
                "progress_cb": self._log_progress_event,
            },
        )
        self._start_task(spec, "Building site...")

    def _on_preview_clicked(self) -> None:
        root = self._current_site_root()
        if root is None:
            QMessageBox.warning(self, "No site root", "Select a site root first.")
            return

        output_dir = self._current_output_dir(root)
        index_path = output_dir / "index.html"
        if not index_path.exists():
            QMessageBox.warning(
                self,
                "Index not found",
                "index.html not found in the output directory.\n"
                "Build the site first or check your output directory.",
            )
            return

        try:
            webbrowser.open(index_path.as_uri())
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
