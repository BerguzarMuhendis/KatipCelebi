from PyQt6.QtCore import QThread, pyqtSignal


class UpdateThread(QThread):
    """Run `shared.update.check_for_update` off the UI thread.

    Emits `result` as (has_update: bool, latest: str, release_url: str).
    """

    result = pyqtSignal(bool, str, str)

    def __init__(self, version: str):
        super().__init__()
        self.version = version

    def run(self) -> None:
        from shared.update import check_for_update

        try:
            has_update, latest, release_url = check_for_update(self.version)
        except Exception:
            has_update, latest, release_url = False, "", ""
        self.result.emit(has_update, latest, release_url)
