import time
from typing import Optional, Type

class LoopTimer:
    """A class-based timer to track and report the progress of a loop.

    Can be used as a standard object or as a context manager.

    Attributes:
        label (str): A descriptive name for the timer instance.
        total (int): The total number of iterations expected in the loop.
        interval (int): How frequently (in iterations) to print progress updates.
        start_time (Optional[float]): The timestamp recorded when the timer
          started.
    """

    def __init__(self, label: str, total_iterations: int, report_interval: int) -> None:
        """Initializes the LoopTimer with configuration settings.

        Args:
            label (str): The name or tag for this specific tracking process.
            total_iterations (int): Total count of iterations in the target loop.
            report_interval (int): Print progress updates every 'm' iterations.
        """
        self.label: str = label
        self.total: int = total_iterations
        self.interval: int = report_interval
        self.start_time: Optional[float] = None

    def __enter__(self) -> "LoopTimer":
        """Enters the runtime context, automatically starting the timer.

        Returns:
            LoopTimer: The timer instance itself.
        """
        self.start()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[object],
    ) -> None:
        """Exits the runtime context, automatically stopping the timer.

        Handles cleanup even if an exception occurs inside the loop block.
        """
        self.stop()

    def start(self) -> None:
        """Starts the internal timer and prints an initial start message."""
        self.start_time = time.time()
        print(f"[{self.label}] Started tracking {self.total} iterations...")

    def update(self, current_iteration: int) -> None:
        """Evaluates progress and prints a status update if the interval is met.

        Args:
            current_iteration (int): The current 1-based loop index.
        """
        if self.start_time is None:
            raise RuntimeError(
                f"Timer '{self.label}' was updated before start() was called."
            )

        # Check if the 1-based loop index matches the interval
        if current_iteration % self.interval == 0 or current_iteration == self.total:
            elapsed: float = time.time() - self.start_time
            percentage: float = (current_iteration / self.total) * 100
            print(
                f"[{self.label}] Progress: {current_iteration}/{self.total} ({percentage:.1f}%) | Elapsed: {elapsed:.2f}s"
            )

    def stop(self) -> None:
        """Stops the internal timer and prints a final execution summary."""
        if self.start_time is None:
            raise RuntimeError(
                f"Timer '{self.label}' was stopped before start() was called."
            )

        total_time: float = time.time() - self.start_time
        print(f"[{self.label}] Completed! Total Time: {total_time:.2f}s")

