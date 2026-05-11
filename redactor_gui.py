#!/usr/bin/env python3
"""GUI interface for the Document Redactor using tkinter.

Provides a user-friendly interface for redacting sensitive information
from PDF, CSV, TXT, and XLSX files.
"""

import os
import sys
import json
import queue
import threading
from pathlib import Path
from tkinter import (
    Tk,
    Frame,
    Label,
    Button,
    Radiobutton,
    StringVar,
    BooleanVar,
    filedialog,
    scrolledtext,
    ttk,
    messagebox,
    Checkbutton,
)

# Add parent directory to path for importing redact_ssns
sys.path.insert(0, str(Path(__file__).parent))

import redact_ssns as redactor


class RedactorGUI:
    """Main GUI application for Document Redactor."""

    CONFIG_FILE = Path.home() / ".redactor_config.json"

    def __init__(self, root):
        self.root = root
        self.root.title("Document Redactor")
        self.root.geometry("700x640")
        self.root.minsize(600, 520)

        # Set window icon (if available)
        try:
            self.root.iconbitmap("redactor.ico")  # Windows
        except:
            pass  # Icon not required

        # Variables
        self.mode_var = StringVar(value="bank")  # Bank mode default
        self.files_var = StringVar()
        self.output_var = StringVar()
        self.recursive_var = BooleanVar(value=False)
        self.pending_custom_phrases = ""
        self.running = False
        self.worker_thread = None
        self.update_queue = queue.Queue()

        # Load saved settings
        self.load_config()

        # Build UI
        self.create_widgets()

        # Start queue checker
        self.check_queue()

    def load_config(self):
        """Load saved configuration."""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    self.output_var.set(config.get("last_output_dir", ""))
                    self.mode_var.set(config.get("last_mode", "bank"))
                    self.pending_custom_phrases = config.get("custom_phrases_text", "")
            except:
                pass

    def save_config(self):
        """Save current settings."""
        config = {
            "last_output_dir": self.output_var.get(),
            "last_mode": self.mode_var.get(),
            "custom_phrases_text": self.custom_phrases_text.get("1.0", "end").rstrip(),
        }
        try:
            with open(self.CONFIG_FILE, "w") as f:
                json.dump(config, f)
        except:
            pass

    def create_widgets(self):
        """Create and layout all GUI widgets."""
        # Main container with padding
        main_frame = Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # Title
        title_label = Label(
            main_frame, text="Document Redactor", font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 5))

        subtitle_label = Label(
            main_frame,
            text="Remove sensitive information from PDFs, CSVs, and Excel files",
            font=("Helvetica", 10),
            fg="gray",
        )
        subtitle_label.pack(pady=(0, 20))

        # File Selection Section
        file_frame = Frame(main_frame)
        file_frame.pack(fill="x", pady=5)

        Label(file_frame, text="Source:", font=("Helvetica", 10, "bold")).pack(
            anchor="w"
        )

        file_input_frame = Frame(file_frame)
        file_input_frame.pack(fill="x", pady=5)

        self.file_entry = ttk.Entry(
            file_input_frame, textvariable=self.files_var, state="readonly"
        )
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ttk.Button(
            file_input_frame, text="Select File(s)", command=self.browse_files
        ).pack(side="left", padx=2)
        ttk.Button(
            file_input_frame, text="Select Folder", command=self.browse_directory
        ).pack(side="left", padx=2)

        # Recursive checkbox
        Checkbutton(
            file_frame,
            text="Include subdirectories (recursive)",
            variable=self.recursive_var,
        ).pack(anchor="w", pady=(5, 0))

        # Mode Selection Section
        mode_frame = Frame(main_frame)
        mode_frame.pack(fill="x", pady=15)

        Label(mode_frame, text="Redaction Mode:", font=("Helvetica", 10, "bold")).pack(
            anchor="w"
        )

        Label(
            mode_frame,
            text="(Used only when the phrase box below is empty)",
            fg="gray",
            font=("Helvetica", 9),
        ).pack(anchor="w")

        modes_frame = Frame(mode_frame)
        modes_frame.pack(fill="x", pady=5)

        modes = [
            (
                "bank",
                "Bank Statement (recommended)\nRedacts numbers, emails, phones, names - preserves $ amounts",
            ),
            ("ssn", "SSN Only\nRedact Social Security Numbers only"),
            ("all", "Comprehensive\nRedact everything (SSNs + bank patterns)"),
        ]

        for value, text in modes:
            Radiobutton(
                modes_frame,
                text=text,
                variable=self.mode_var,
                value=value,
                justify="left",
                padx=10,
                pady=5,
            ).pack(anchor="w", pady=2)

        # Custom phrases (optional)
        custom_frame = Frame(main_frame)
        custom_frame.pack(fill="both", expand=False, pady=(5, 10))

        Label(
            custom_frame,
            text="Phrases to redact only (optional):",
            font=("Helvetica", 10, "bold"),
        ).pack(anchor="w")

        Label(
            custom_frame,
            text="Comma- or newline-separated. If you enter anything here, only these "
            "literals are redacted and the mode above is skipped. Case-insensitive.",
            fg="gray",
            font=("Helvetica", 9),
        ).pack(anchor="w")

        self.custom_phrases_text = scrolledtext.ScrolledText(
            custom_frame, wrap="word", height=4, bg="#fafafa"
        )
        self.custom_phrases_text.pack(fill="both", expand=False, pady=(4, 0))
        if self.pending_custom_phrases:
            self.custom_phrases_text.insert("1.0", self.pending_custom_phrases)

        # Output Directory Section
        output_frame = Frame(main_frame)
        output_frame.pack(fill="x", pady=5)

        Label(
            output_frame,
            text="Output Directory (optional):",
            font=("Helvetica", 10, "bold"),
        ).pack(anchor="w")

        output_input_frame = Frame(output_frame)
        output_input_frame.pack(fill="x", pady=5)

        ttk.Entry(output_input_frame, textvariable=self.output_var).pack(
            side="left", fill="x", expand=True, padx=(0, 5)
        )
        ttk.Button(output_input_frame, text="Browse", command=self.browse_output).pack(
            side="left"
        )

        Label(
            output_frame,
            text="Leave empty to save redacted files next to originals",
            fg="gray",
        ).pack(anchor="w")

        # Action Buttons
        action_frame = Frame(main_frame)
        action_frame.pack(fill="x", pady=15)

        self.start_button = ttk.Button(
            action_frame,
            text="▶  START REDACTION",
            command=self.start_redaction,
            style="Accent.TButton",
        )
        self.start_button.pack(side="left", padx=(0, 10))

        self.cancel_button = ttk.Button(
            action_frame,
            text="✕ Cancel",
            command=self.cancel_redaction,
            state="disabled",
        )
        self.cancel_button.pack(side="left", padx=(0, 10))

        ttk.Button(
            action_frame, text="Open Output Folder", command=self.open_output_folder
        ).pack(side="left", padx=(0, 10))
        ttk.Button(action_frame, text="Clear Log", command=self.clear_log).pack(
            side="left"
        )

        # Progress Section
        progress_frame = Frame(main_frame)
        progress_frame.pack(fill="x", pady=5)

        self.progress_label = Label(progress_frame, text="Ready")
        self.progress_label.pack(anchor="w")

        self.progress_bar = ttk.Progressbar(
            progress_frame, mode="indeterminate", length=400
        )
        self.progress_bar.pack(fill="x", pady=5)

        # Log Window
        log_frame = Frame(main_frame)
        log_frame.pack(fill="both", expand=True, pady=5)

        Label(log_frame, text="Log:", font=("Helvetica", 10, "bold")).pack(anchor="w")

        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap="word", height=10, state="disabled", bg="#f5f5f5"
        )
        self.log_text.pack(fill="both", expand=True, pady=5)

        # Status bar
        self.status_label = Label(
            main_frame, text="Ready", bd=1, relief="sunken", anchor="w"
        )
        self.status_label.pack(fill="x", side="bottom", pady=(10, 0))

    def browse_files(self):
        """Open file picker for selecting files."""
        files = filedialog.askopenfilenames(
            title="Select Files to Redact",
            filetypes=[
                ("All supported files", "*.pdf *.csv *.txt *.xlsx *.xlsm"),
                ("PDF files", "*.pdf"),
                ("CSV files", "*.csv"),
                ("Text files", "*.txt"),
                ("Excel files", "*.xlsx *.xlsm"),
                ("All files", "*.*"),
            ],
        )
        if files:
            if len(files) == 1:
                self.files_var.set(files[0])
            else:
                self.files_var.set(f"{len(files)} files selected")
            self.selected_files = list(files)
            self.log(f"Selected {len(files)} file(s)")

    def browse_directory(self):
        """Open directory picker for batch processing."""
        directory = filedialog.askdirectory(title="Select Directory to Process")
        if directory:
            self.files_var.set(directory)
            self.selected_files = [directory]
            self.log(f"Selected directory: {directory}")

    def browse_output(self):
        """Open directory picker for output location."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_var.set(directory)
            self.save_config()

    def log(self, message):
        """Add message to log window."""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_log(self):
        """Clear the log window."""
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.configure(state="disabled")

    def open_output_folder(self):
        """Open the output folder in file manager."""
        output_dir = self.output_var.get()
        if not output_dir:
            # Use first file's directory
            if hasattr(self, "selected_files") and self.selected_files:
                output_dir = str(Path(self.selected_files[0]).parent)
            else:
                messagebox.showwarning(
                    "No Output", "No output directory specified and no files selected."
                )
                return

        # Open folder based on OS
        if sys.platform == "darwin":  # macOS
            os.system(f'open "{output_dir}"')
        elif sys.platform == "win32":  # Windows
            os.system(f'start "" "{output_dir}"')
        else:  # Linux
            os.system(f'xdg-open "{output_dir}"')

    def start_redaction(self):
        """Start the redaction process in a worker thread."""
        if not hasattr(self, "selected_files") or not self.selected_files:
            messagebox.showwarning(
                "No Selection", "Please select file(s) or a directory first."
            )
            return

        self.running = True
        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.progress_bar.start(10)
        self.progress_label.configure(text="Processing...")
        self.status_label.configure(text="Processing files...")

        # Save config
        self.save_config()

        # Start worker thread
        self.worker_thread = threading.Thread(target=self.redaction_worker, daemon=True)
        self.worker_thread.start()

    def cancel_redaction(self):
        """Cancel the ongoing redaction process."""
        if self.running:
            self.running = False
            self.log("Cancelling... (will stop after current file)")
            self.status_label.configure(text="Cancelling...")
            self.cancel_button.configure(state="disabled")

    def redaction_worker(self):
        """Worker thread for redaction processing."""
        mode = self.mode_var.get()
        output_dir = self.output_var.get() or None
        recursive = self.recursive_var.get()

        raw_phrases = self.custom_phrases_text.get("1.0", "end")
        lines = [ln.strip() for ln in raw_phrases.splitlines() if ln.strip()]
        custom_phrases = redactor.parse_user_phrase_inputs(lines)

        files_to_process = []

        # Collect files
        for path in self.selected_files:
            path_obj = Path(path)
            if path_obj.is_file():
                files_to_process.append(path_obj)
            elif path_obj.is_dir():
                if recursive:
                    for ext in ["*.pdf", "*.csv", "*.txt", "*.xlsx", "*.xlsm"]:
                        files_to_process.extend(path_obj.rglob(ext))
                else:
                    for ext in ["*.pdf", "*.csv", "*.txt", "*.xlsx", "*.xlsm"]:
                        files_to_process.extend(path_obj.glob(ext))

        # Remove duplicates and redacted files
        files_to_process = sorted(
            set(f for f in files_to_process if "_redacted" not in f.stem)
        )

        if not files_to_process:
            self.update_queue.put(("error", "No supported files found."))
            return

        total_files = len(files_to_process)
        total_redactions = 0

        self.update_queue.put(("status", f"Found {total_files} file(s) to process"))

        for i, file_path in enumerate(files_to_process, 1):
            if not self.running:
                self.update_queue.put(("log", "Cancelled by user."))
                break

            self.update_queue.put(
                ("log", f"[{i}/{total_files}] Processing: {file_path.name}")
            )
            self.update_queue.put(("progress", f"{i}/{total_files}"))

            try:
                # Determine output path
                if output_dir:
                    output_path = (
                        Path(output_dir)
                        / f"{file_path.stem}_redacted{file_path.suffix}"
                    )
                else:
                    output_path = None

                # Perform redaction
                count = redactor.redact_file(
                    file_path,
                    output_path=output_path,
                    mode=mode,
                    verbose=False,
                    custom_phrases=custom_phrases,
                )

                total_redactions += count

                if count > 0:
                    out_path = output_path or file_path.with_name(
                        f"{file_path.stem}_redacted{file_path.suffix}"
                    )
                    self.update_queue.put(
                        ("log", f"  ✓ Redacted {count} item(s) → {out_path.name}")
                    )
                else:
                    if custom_phrases:
                        self.update_queue.put(
                            ("log", f"  ℹ No matches for the listed phrase(s)")
                        )
                    else:
                        self.update_queue.put(("log", f"  ℹ No sensitive data found"))

            except Exception as e:
                self.update_queue.put(("error", f"  ✗ Error: {str(e)}"))

        # Completion
        mode_desc = {
            "ssn": "SSN(s)",
            "bank": "bank-sensitive item(s)",
            "all": "item(s)",
        }
        if custom_phrases:
            desc = "listed phrase occurrence(s)"
        else:
            desc = mode_desc[mode]
        if self.running:
            self.update_queue.put(
                (
                    "complete",
                    f"Complete: {total_files} file(s), {total_redactions} {desc} redacted.",
                )
            )
        else:
            self.update_queue.put(
                (
                    "complete",
                    f"Cancelled. Processed {i - 1}/{total_files} files, {total_redactions} {desc} redacted.",
                )
            )

    def check_queue(self):
        """Check for updates from worker thread."""
        try:
            while True:
                msg_type, message = self.update_queue.get_nowait()

                if msg_type == "log":
                    self.log(message)
                elif msg_type == "status":
                    self.status_label.configure(text=message)
                elif msg_type == "progress":
                    self.progress_label.configure(text=f"Progress: {message}")
                elif msg_type == "error":
                    self.log(message)
                    self.progress_label.configure(text="Error")
                elif msg_type == "complete":
                    self.log(message)
                    self.progress_label.configure(text="Complete")
                    self.progress_bar.stop()
                    self.start_button.configure(state="normal")
                    self.cancel_button.configure(state="disabled")
                    self.status_label.configure(text="Ready")
                    self.running = False

                    # Show completion dialog
                    if "Error" not in message:
                        messagebox.showinfo("Complete", message)
        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self.check_queue)

    def run(self):
        """Start the GUI event loop."""
        self.root.mainloop()


def main():
    """Entry point for GUI mode."""
    root = Tk()
    app = RedactorGUI(root)
    app.run()


if __name__ == "__main__":
    main()
