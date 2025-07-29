import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QPushButton, QListWidget, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QProgressBar, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal, QObject, QPropertyAnimation, QRect, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QMovie, QPixmap, QIcon
from scrapers import get_scraper_for_url

class DownloadWorker(QObject):
    chapters_fetched = Signal(list, str)
    chapter_status = Signal(int, str)
    chapter_retry_enabled = Signal(int, bool)
    progress = Signal(int)
    log = Signal(str)
    finished = Signal()

    def __init__(self, url, lang):
        super().__init__()
        self.url = url
        self.lang = lang
        self.scraper = None
        self.chapters = []
        self.title = None
        self._should_stop = False

    def stop(self):
        self._should_stop = True

    def run(self):
        self.scraper = get_scraper_for_url(self.url)
        if not self.scraper:
            self.log.emit("No scraper found for this URL.")
            self.finished.emit()
            return
        try:
            chapters = self.scraper.get_chapters(self.url, self.lang)
            if not chapters:
                self.log.emit("No chapters found.")
                self.finished.emit()
                return
            self.chapters = chapters
            self.title = chapters[0].get("title") or self.url.split("/title/")[-1].split("/")[1] if "/title/" in self.url else "manga"
            self.chapters_fetched.emit(chapters, self.title)
            total = len(chapters)
            completed = 0
            for i, ch in enumerate(chapters):
                if self._should_stop:
                    break
                chapter_id = ch["id"]
                chapter_num = ch["chapter"]
                folder = os.path.join("downloads", self.title, f"Chapter_{chapter_num}")
                self.chapter_status.emit(i, "Downloading...")
                try:
                    ok = self.scraper.download_chapter(chapter_id, folder)
                    if ok:
                        self.chapter_status.emit(i, "Completed")
                        self.chapter_retry_enabled.emit(i, False)
                    else:
                        self.chapter_status.emit(i, "Failed")
                        self.chapter_retry_enabled.emit(i, True)
                except Exception as e:
                    self.chapter_status.emit(i, "Failed")
                    self.chapter_retry_enabled.emit(i, True)
                    self.log.emit(f"Error downloading chapter {chapter_num}: {e}")
                completed += 1
                self.progress.emit(int(completed / total * 100))
            self.log.emit("All downloads attempted.")
        except Exception as e:
            self.log.emit(f"Error fetching chapters: {e}")
        self.finished.emit()

    def retry_chapter(self, row):
        ch = self.chapters[row]
        chapter_id = ch["id"]
        chapter_num = ch["chapter"]
        folder = os.path.join("downloads", self.title, f"Chapter_{chapter_num}")
        self.chapter_status.emit(row, "Retrying...")
        try:
            ok = self.scraper.download_chapter(chapter_id, folder)
            if ok:
                self.chapter_status.emit(row, "Completed")
                self.chapter_retry_enabled.emit(row, False)
            else:
                self.chapter_status.emit(row, "Failed")
                self.chapter_retry_enabled.emit(row, True)
        except Exception as e:
            self.chapter_status.emit(row, "Failed")
            self.chapter_retry_enabled.emit(row, True)
            self.log.emit(f"Error retrying chapter {chapter_num}: {e}")

class CollapsibleSection(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.is_expanded = False
        self.setup_ui(title)
        
    def setup_ui(self, title):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header button
        self.header_btn = QPushButton(title)
        self.header_btn.setStyleSheet("""
            QPushButton {
                background: #393e6e;
                color: #fff;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                text-align: left;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #4a4f7f;
            }
        """)
        self.header_btn.clicked.connect(self.toggle)
        layout.addWidget(self.header_btn)
        
        # Content area
        self.content_widget = QWidget()
        self.content_widget.setMaximumHeight(0)
        self.content_widget.setStyleSheet("""
            QWidget {
                background: #2a2e4a;
                border-radius: 8px;
                margin-top: 4px;
            }
        """)
        layout.addWidget(self.content_widget)
        
        # Animation
        self.animation = QPropertyAnimation(self.content_widget, b"maximumHeight")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        
    def toggle(self):
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()
            
    def expand(self):
        self.is_expanded = True
        self.animation.setStartValue(0)
        self.animation.setEndValue(self.content_widget.sizeHint().height())
        self.animation.start()
        self.header_btn.setText("▼ Supported Websites")
        
    def collapse(self):
        self.is_expanded = False
        self.animation.setStartValue(self.content_widget.height())
        self.animation.setEndValue(0)
        self.animation.start()
        self.header_btn.setText("▶ Supported Websites")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manhwa Ripper")
        self.resize(950, 750)

        # Set custom app icon
        self.set_app_icon()

        # Central widget and main layout
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)

        # Colorful, dark header/banner with app icon
        header_layout = QHBoxLayout()
        
        # Left app icon
        left_icon = QLabel()
        left_icon.setPixmap(self.get_app_icon_pixmap(64, 64))
        left_icon.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(left_icon)
        
        # Title
        header = QLabel("Manhwa Ripper")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Comic Sans MS", 32, QFont.Bold))
        header.setStyleSheet("color: #fff; background: transparent;")
        header_layout.addWidget(header)
        
        # Right app icon
        right_icon = QLabel()
        right_icon.setPixmap(self.get_app_icon_pixmap(64, 64))
        right_icon.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(right_icon)
        
        # Header container with gradient background
        header_container = QWidget()
        header_container.setLayout(header_layout)
        header_container.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #393e6e, stop:1 #232946); border-radius: 18px; padding: 18px 0; margin-bottom: 12px;")
        main_layout.addWidget(header_container)

        # URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("Webcomic URL:")
        url_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        url_label.setStyleSheet("color: #f4f4f4;")
        self.url_input = QLineEdit()
        self.url_input.setStyleSheet("padding: 8px; border-radius: 8px; border: 1px solid #393e6e; background: #232946; color: #fff;")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        main_layout.addLayout(url_layout)

        # Language selection
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Language:")
        lang_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lang_label.setStyleSheet("color: #f4f4f4;")
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("Spanish", "es")
        self.lang_combo.addItem("French", "fr")
        self.lang_combo.addItem("All", "all")
        self.lang_combo.setStyleSheet("padding: 8px; border-radius: 8px; border: 1px solid #393e6e; background: #232946; color: #fff;")
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        main_layout.addLayout(lang_layout)

        # Supported websites section
        self.supported_sites_section = CollapsibleSection("▶ Supported Websites")
        self.setup_supported_sites_content()
        main_layout.addWidget(self.supported_sites_section)

        # Download button
        self.download_btn = QPushButton("Start Download")
        self.download_btn.setStyleSheet("background: #ffb6c1; color: #232946; font-weight: bold; border-radius: 10px; padding: 10px 0; font-size: 16px;")
        main_layout.addWidget(self.download_btn)

        # Chapter progress table
        self.chapter_table = QTableWidget(0, 3)
        self.chapter_table.setHorizontalHeaderLabels(["Chapter", "Status", "Action"])
        self.chapter_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.chapter_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.chapter_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.chapter_table.setStyleSheet("background: #393e6e; color: #fff; border-radius: 10px; font-size: 14px;")
        main_layout.addWidget(QLabel("<span style='color:#f4f4f4;'>Chapter Progress:</span>"))
        main_layout.addWidget(self.chapter_table)

        # Standard progress bar (replaces animated GIF)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #2e2e3a;
                color: #4f8cff;
                border-radius: 10px;
                height: 30px;
                font-size: 16px;
                font-weight: bold;
                text-align: center;
            }
            QProgressBar::chunk {
                background: #4f8cff;
                border-radius: 10px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # Status/progress log
        main_layout.addWidget(QLabel("<span style='color:#f4f4f4;'>Log:</span>"))
        self.status_list = QListWidget()
        self.status_list.setMaximumHeight(120)
        self.status_list.setStyleSheet("background: #393e46; color: #fff; border-radius: 10px; font-size: 13px;")
        main_layout.addWidget(self.status_list)

        # Apply overall stylesheet
        self.setStyleSheet("QWidget { background: #232946; } QLabel { font-family: 'Segoe UI', sans-serif; } QPushButton:hover { background: #87cefa; color: #232946; }")

        # Connect button
        self.download_btn.clicked.connect(self.on_start_download)

        # Store chapters and worker
        self.chapters = []
        self.worker = None
        self.worker_thread = None
        self.title = None
        self._progress = 0

    def setup_supported_sites_content(self):
        """Setup the content for the supported websites section."""
        content_layout = QVBoxLayout(self.supported_sites_section.content_widget)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(8)
        
        # Title
        title_label = QLabel("Currently Supported Sites:")
        title_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title_label.setStyleSheet("color: #ffb6c1; margin-bottom: 8px;")
        content_layout.addWidget(title_label)
        
        # Site list
        sites = [
            ("🎯 MangaDex", "mangadex.org - Official API support"),
            ("🧽 Asura Scans", "asurascanlation.com, asurascans.com, asura.gg, asura.xyz, etc."),
            ("⚡ Reaper Scans", "reaperscans.com - WordPress-based site"),
            ("🔥 Flame Scans", "flamescans.org - WordPress-based site"),
            ("🌐 Generic WordPress Sites", "Automatically detects most WordPress manga sites")
        ]
        
        for site_name, description in sites:
            site_layout = QHBoxLayout()
            
            # Site name
            name_label = QLabel(site_name)
            name_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
            name_label.setStyleSheet("color: #87cefa; min-width: 200px;")
            site_layout.addWidget(name_label)
            
            # Description
            desc_label = QLabel(description)
            desc_label.setFont(QFont("Segoe UI", 9))
            desc_label.setStyleSheet("color: #ccc;")
            desc_label.setWordWrap(True)
            site_layout.addWidget(desc_label)
            
            content_layout.addLayout(site_layout)
        
        # Note
        note_label = QLabel("💡 Tip: Most WordPress-based manga sites are automatically supported!")
        font = QFont("Segoe UI", 9)
        font.setItalic(True)
        note_label.setFont(font)
        note_label.setStyleSheet("color: #ffd700; margin-top: 8px; padding: 8px; background: rgba(255, 215, 0, 0.1); border-radius: 4px;")
        content_layout.addWidget(note_label)

    def set_app_icon(self):
        """Set the custom app icon."""
        try:
            # Try to load the icon from the resources
            icon_path = os.path.join(os.path.dirname(__file__), "app_icon.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                # Fallback: create a simple colored icon
                self.create_fallback_icon()
        except Exception as e:
            print(f"Could not set app icon: {e}")
            self.create_fallback_icon()

    def get_app_icon_pixmap(self, width, height):
        """Get the app icon as a pixmap for use in the UI."""
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "app_icon.png")
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                return pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                # Fallback: create a simple colored square
                pixmap = QPixmap(width, height)
                pixmap.fill(Qt.yellow)  # Spongebob's color!
                return pixmap
        except Exception as e:
            print(f"Could not load app icon pixmap: {e}")
            # Fallback: create a simple colored square
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.yellow)
            return pixmap

    def create_fallback_icon(self):
        """Create a simple fallback icon if the image file is not available."""
        try:
            # Create a simple colored square as fallback
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.yellow)  # Spongebob's color!
            self.setWindowIcon(QIcon(pixmap))
        except Exception as e:
            print(f"Could not create fallback icon: {e}")

    def on_start_download(self):
        url = self.url_input.text().strip()
        lang = self.lang_combo.currentData()
        self.status_list.addItem(f"Starting download for: {url} (Language: {lang})")
        self.download_btn.setEnabled(False)
        self.chapter_table.setRowCount(0)
        self.set_progress(0)
        # Start worker thread
        self.worker = DownloadWorker(url, lang)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.chapters_fetched.connect(self.populate_chapter_table)
        self.worker.chapter_status.connect(self.update_chapter_status)
        self.worker.chapter_retry_enabled.connect(self.enable_retry)
        self.worker.progress.connect(self.set_progress)
        self.worker.log.connect(self.log)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker_thread.start()

    def set_progress(self, percent):
        self._progress = percent
        self.progress_bar.setValue(percent)

    def resizeEvent(self, event):
        # Make progress_bg responsive to window size
        new_width = max(300, self.width() - 300)
        # self.progress_bg.setFixedWidth(new_width) # This line is removed as progress_bg is removed
        self.set_progress(self._progress)
        super().resizeEvent(event)

    def populate_chapter_table(self, chapters, title):
        self.chapters = chapters
        self.title = title
        self.chapter_table.setRowCount(0)
        for i, ch in enumerate(chapters):
            self.chapter_table.insertRow(i)
            self.chapter_table.setItem(i, 0, QTableWidgetItem(str(ch["chapter"])))
            self.chapter_table.setItem(i, 1, QTableWidgetItem("Pending"))
            retry_btn = QPushButton("Retry")
            retry_btn.clicked.connect(lambda _, row=i: self.retry_chapter(row))
            retry_btn.setStyleSheet("background: #87cefa; color: #fff; border-radius: 8px; font-weight: bold;")
            self.chapter_table.setCellWidget(i, 2, retry_btn)
            retry_btn.setEnabled(False)

    def update_chapter_status(self, row, status):
        self.chapter_table.setItem(row, 1, QTableWidgetItem(status))

    def enable_retry(self, row, enabled):
        btn = self.chapter_table.cellWidget(row, 2)
        if btn:
            btn.setEnabled(enabled)

    def retry_chapter(self, row):
        if self.worker:
            self.worker.retry_chapter(row)

    def log(self, msg):
        self.status_list.addItem(str(msg))

    def on_worker_finished(self):
        self.download_btn.setEnabled(True) 