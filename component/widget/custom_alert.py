from sepal_ui import color
from sepal_ui import sepalwidgets as sw
from tqdm.notebook import tqdm


class CustomAlert(sw.Alert):
    """Custom alert that update the progress iteratively."""

    total_image: int = 0

    progress_text: str = ""

    current_progress = 0

    def _update_progress(
        self, progress: float, msg: str = "Progress", **tqdm_args
    ) -> None:
        """Update the Alert message with a tqdm progress bar.

        .. note::

            set the ``total`` argumentent of tqdm to use different values than [0, 1]

        Args:
            progress: the progress status in float
            msg: The message to use before the progress bar
            tqdm_args (optional): any arguments supported by a tqdm progress bar, they will only be taken into account after a call to ``self.reset()``.
        """
        print("new")
        # show the alert
        self.show()

        # cast the progress to float and perform sanity checks
        progress = float(progress)
        if self.progress_output not in self.children:
            total = tqdm_args.get("total", 1)
        else:
            total = self.progress_bar.total
            self.progress_bar.desc = msg

        if not (0 <= progress <= total):
            raise ValueError(f"progress should be in [0, {total}], {progress} given")

        # Prevent adding multiple times
        if self.progress_output not in self.children:

            self.children = [self.progress_output]

            tqdm_args.setdefault("bar_format", "{l_bar}{bar}{n_fmt}/{total_fmt}")
            tqdm_args.setdefault("dynamic_ncols", False)
            tqdm_args.setdefault("total", 1)
            tqdm_args.setdefault("desc", msg)
            tqdm_args.setdefault("colour", getattr(color, self.type))

            with self.progress_output:
                self.progress_output.clear_output()
                self.progress_bar = tqdm(**tqdm_args)
                self.progress_bar.container.children[0].add_class(f"{self.type}--text")
                self.progress_bar.container.children[2].add_class(f"{self.type}--text")

                # Initialize bar
                self.progress_bar.update(0)

        self.progress_bar.update(progress - self.progress_bar.n)

    def reset_progress(self, total_image=1, progress_text=""):
        """rest progress and setup the totla_image value and the text."""

        self.total_image = total_image
        self.progress_text = progress_text
        self.current_progress = 0

        self._update_progress(0, self.progress_text, total=self.total_image)

        self.progress_bar.total = self.total_image

    def update_progress(self) -> None:
        """increment the progressses by 1."""

        self.current_progress = self.current_progress + 1
        self._update_progress(
            progress=self.current_progress,
            msg=self.progress_text,
            total=self.total_image,
        )
        # print("####", self.current_progress, self.total_image, self.progress_text)
