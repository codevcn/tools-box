from PySide6.QtCore import QElapsedTimer


class PerformanceTestingMixin:
    def __init__(self, *args, **kwargs):
        self._perf_timer = QElapsedTimer()
        self._perf_timer.start()
        self._measured_time = 0.0
        super().__init__(*args, **kwargs)  # quan trọng: cho MRO chạy tới QWidget

    def showEvent(self, event):
        super().showEvent(event)  # type: ignore
        className = self.__class__.__name__
        measured_time = self._perf_timer.elapsed()
        if className == "MainWindow":
            self._measured_time = measured_time
        print(f">>> first show {self.__class__.__name__} after {measured_time} ms")
