from sepal_ui import sepalwidgets as sw


class CustomAlert(sw.Alert):
    """Custom alert that update the progress iteratively."""

    total_image: int = 0

    progress_text: str = ""

    current_progress = 0

    def reset_progress(self, total_image=1, progress_text=""):
        """rest progress and setup the totla_image value and the text."""
        self.total_image = total_image
        self.progress_text = progress_text
        self.current_progress = 0

        super().update_progress(0, self.progress_text, total=self.total_image)

        self.progress_bar.total = self.total_image

    def update_progress(self) -> None:
        """increment the progressses by 1."""

        self.current_progress = self.current_progress + 1
        super().update_progress(
            progress=self.current_progress,
            msg=self.progress_text,
            total=self.total_image,
        )
        # print("####", self.current_progress, self.total_image, self.progress_text)
