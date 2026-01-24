from PySide6.QtCore import QObject, Signal, QProcess


class RcloneDriveSetup(QObject):
    log = Signal(str)
    done = Signal(bool, str)  # (ok, message)

    def __init__(self, rclone_exe: str = "rclone", parent=None):
        super().__init__(parent)
        self._rclone_exe: str = rclone_exe
        self._process: QProcess = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._ended_steps_successfully: bool = False

        self._process.readyReadStandardOutput.connect(self._on_ready_read)
        self._process.finished.connect(self._on_finished)

        self._queue: list[list[str]] = []
        self._current_step = ""

    def is_running(self) -> bool:
        return self._process.state() == QProcess.ProcessState.Running

    def setup_drive_remote(self, remote_name: str, *, scope: str = "drive") -> None:
        # tạo remote (không token)
        # rồi reconnect để rclone tự login + lưu token
        self._queue = [
            ["config", "create", remote_name, "drive", f"scope={scope}"],
            ["config", "reconnect", f"{remote_name}:"],
        ]
        self._run_next()

    def _run_next(self) -> None:
        if not self._queue and self._ended_steps_successfully:
            self.done.emit(True, "Remote đã được tạo và đăng nhập thành công.")
        else:
            args = self._queue.pop(0)
            self._current_step = " ".join(args)
            self.log.emit(f">>> rclone {self._current_step}")
            self._process.start(self._rclone_exe, args)

            if not self._process.waitForStarted(3000):
                self.done.emit(
                    False, "Không chạy được rclone. Kiểm tra PATH hoặc rclone_exe."
                )

    def _on_ready_read(self) -> None:
        text = bytes(self._process.readAllStandardOutput().data()).decode(
            "utf-8", errors="replace"
        )
        if not text.strip():
            return
        self.log.emit(f">>> {text.rstrip()}")
        # detect câu hỏi refresh token từ rclone
        self._handle_interactive_question(text)

    def _on_finished(self, exit_code: int, _status) -> None:
        if exit_code != 0:
            # lỗi khi chạy step hiện tại
            self.done.emit(
                False,
                f"Lỗi khi chạy: rclone {self._current_step} (exit_code={exit_code})",
            )
            self._queue = []
        else:
            # chạy step tiếp theo
            if not self._queue:
                self._ended_steps_successfully = True
            self._run_next()

    def _handle_interactive_question(self, text: str) -> None:
        """
        Auto-handle các câu hỏi interactive của rclone khi config/reconnect Google Drive.

        Auto được:
        - Use web browser to automatically authenticate? -> y/n
        - Already have a token - refresh? -> y/n
        - Shared Drive (Team Drive)? -> y/n
        - Use auto config? -> y (thường)
        - Edit advanced config? -> n (thường)
        - Configure as Shared Drive? -> n (thường)

        Không auto được (cần user):
        - Enter verification code / paste code (nếu chọn headless / không browser)
        """

        if not getattr(self, "_process", None):
            return

        # init flags chống spam write
        if not hasattr(self, "_answered"):
            self._answered = set()

        t = (text or "").lower()

        def answer_once(key: str, payload: bytes, log_line: str) -> None:
            if key in self._answered:
                return
            self._answered.add(key)
            try:
                self.log.emit(log_line)
                self._process.write(payload)
            except Exception as e:
                self.log.emit(f">>> failed to write answer ({key}): {e}")

        # ------------------------
        # 1) Use web browser to automatically authenticate?
        # ------------------------
        if "use web browser to automatically authenticate" in t:
            use_browser = True  # default True
            answer_once(
                "use_browser_auth",
                b"y\n" if use_browser else b"n\n",
                f">>> auto-answer: use browser auth -> {'y' if use_browser else 'n'}",
            )
            return

        # ------------------------
        # 2) Use auto config?  (thường xuất hiện nếu chọn headless/no-browser)
        # rclone wording hay gặp: "Use auto config?"
        # ------------------------
        if "use auto config" in t and ("y) yes" in t or "y/n" in t or "(y/n" in t):
            # Thường: y nếu bạn có thể mở browser (auto config), n nếu headless
            use_auto = True
            answer_once(
                "use_auto_config",
                b"y\n" if use_auto else b"n\n",
                f">>> auto-answer: use auto config -> {'y' if use_auto else 'n'}",
            )
            return

        # ------------------------
        # 3) Already have a token - refresh?
        # ------------------------
        if "already have a token" in t and "refresh" in t:
            refresh = False  # default False
            answer_once(
                "refresh_token",
                b"y\n" if refresh else b"n\n",
                f">>> auto-answer: refresh token -> {'y' if refresh else 'n'}",
            )
            return

        # ------------------------
        # 4) Shared Drive / Team Drive?
        # ------------------------
        # Các biến thể:
        # - "Configure this as a Shared Drive (Team Drive)?"
        # - "Configure this as a Shared Drive?"
        if ("shared drive" in t or "team drive" in t) and (
            "y) yes" in t or "y/n" in t or "(y/n" in t
        ):
            use_shared = False  # default False
            answer_once(
                "use_shared_drive",
                b"y\n" if use_shared else b"n\n",
                f">>> auto-answer: shared/team drive -> {'y' if use_shared else 'n'}",
            )
            return

        # ------------------------
        # 5) Edit advanced config?
        # ------------------------
        # Thường xuất hiện trong wizard config: "Edit advanced config?"
        if "edit advanced config" in t and ("y) yes" in t or "y/n" in t or "(y/n" in t):
            edit_advanced = False  # default False
            answer_once(
                "edit_advanced_config",
                b"y\n" if edit_advanced else b"n\n",
                f">>> auto-answer: edit advanced config -> {'y' if edit_advanced else 'n'}",
            )
            return

        # # ------------------------
        # # 6) Prompts cần user nhập code (KHÔNG auto)
        # # ------------------------
        # # Các biến thể hay gặp:
        # # - "Enter verification code"
        # # - "Enter the code you received"
        # # - "Paste the following into your browser"
        # # - "Enter a string value. Press Enter for the default"
        # #
        # # Với tool UI của bạn: nên hiển thị hướng dẫn cho user.
        # if "enter verification code" in t or "enter the code" in t:
        #     if "need_verification_code" not in self._answered:
        #         self._answered.add("need_verification_code")
        #         msg = (
        #             "Rclone đang yêu cầu Verification Code.\n"
        #             "- Nếu bạn chọn NO browser/headless, rclone sẽ đưa 1 URL để bạn mở trên máy có browser.\n"
        #             "- Sau khi login xong, Google sẽ trả về code, bạn paste code đó vào đây.\n"
        #         )
        #         # Nếu bạn có signal need_user_input:
        #         if hasattr(self, "need_user_input"):
        #             self.need_user_input.emit(msg)
        #         else:
        #             self.log.emit(">>> NEED USER INPUT: verification code required")
        #             self.log.emit(msg)
        #     return

        # if (
        #     "paste the following into your browser" in t
        #     or "open the following link" in t
        # ):
        #     # Đây thường là phần rclone in URL để user mở
        #     # Bạn chỉ cần log lại cho user thấy (đã log ở _on_ready_read rồi),
        #     # và nếu muốn thì emit thêm signal.
        #     if "need_open_url" not in self._answered:
        #         self._answered.add("need_open_url")
        #         msg = (
        #             "Rclone yêu cầu bạn mở URL trong browser để lấy code (headless flow).\n"
        #             "Hãy xem URL trong log và mở nó, sau đó paste code khi được hỏi."
        #         )
        #         if hasattr(self, "need_user_input"):
        #             self.need_user_input.emit(msg)
        #         else:
        #             self.log.emit(">>> NEED USER ACTION: open URL shown in log")
        #     return

    def cancel_process(self, wait_ms: int = 0) -> None:
        if self._process.state() == QProcess.ProcessState.NotRunning:
            self._queue = []
            return

        self.log.emit(">>> Đang hủy process...")
        self._process.terminate()

        if wait_ms > 0:
            if not self._process.waitForFinished(wait_ms):
                self._process.kill()
                self._process.waitForFinished(500)

        self._queue = []
        self.log.emit(">>> Process đã dừng")
