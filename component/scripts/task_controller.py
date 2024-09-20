import threading


class TaskController:
    def __init__(
        self,
        start_button,
        stop_button,
        alert,
        function,
        callback=None,
        *function_args,
        **function_kwargs,
    ):
        self.alert = alert
        self.task_thread = None
        self.function = function
        self.function_args = function_args
        self.function_kwargs = function_kwargs
        self.shared_variable = threading.Event()
        self.callback = callback

        self.start_button = start_button
        self.stop_button = stop_button

        stop_button.on_event("click", self.stop_task)

    def long_running_task(self):
        try:
            self.alert.reset()
            self.start_button.loading = True
            result = self.function(
                self.shared_variable, *self.function_args, **self.function_kwargs
            )
            if self.callback:
                self.callback(result)
        except Exception as e:
            self.alert.append_msg(f"Error occurred: {e}", type_="error")
            raise e
        finally:
            self.start_button.loading = False

    def start_task(self, *args):
        self.shared_variable.clear()
        self.start_button.loading = True
        self.task_thread = threading.Thread(target=self.long_running_task)
        self.task_thread.start()

    def stop_task(self, *args):
        self.stop_button.loading = True
        self.shared_variable.set()
        if self.task_thread is not None:
            self.task_thread.join()
        self.start_button.loading = False
        self.stop_button.loading = False
        self.start_button.disabled = False

        print("stopped")
        self.alert.append_msg(
            "The process was interrupted by the user.", type_="warning"
        )

        print("Task thread stopped.")
