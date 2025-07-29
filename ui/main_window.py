import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QPushButton, QListWidget, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal, QObject, QPropertyAnimation, QRect
from PySide6.QtGui import QFont, QMovie, QPixmap
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manhwa Ripper")
        self.resize(950, 750)

        # Central widget and main layout
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)

        # Colorful, dark header/banner
        header = QLabel("\u2728 Manhwa Ripper \u2728")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Comic Sans MS", 32, QFont.Bold))
        header.setStyleSheet("color: #fff; background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #393e6e, stop:1 #232946); border-radius: 18px; padding: 18px 0; margin-bottom: 12px;")
        main_layout.addWidget(header)

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