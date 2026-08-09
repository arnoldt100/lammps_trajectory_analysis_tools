import pytest
from unittest.mock import patch
from your_module import LoopTimer  # Replace 'your_module' with your actual file name

def test_timer_initialization() -> None:
    """Verify that the timer properties are correctly assigned on creation."""
    timer = LoopTimer(label="Test", total_iterations=10, report_interval=2)
    assert timer.label == "Test"
    assert timer.total == 10
    assert timer.interval == 2
    assert timer.start_time is None

def test_timer_start(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that starting the timer sets the timestamp and prints a message."""
    timer = LoopTimer(label="Process", total_iterations=50, report_interval=10)
    
    with patch("time.time", return_value=1000.0):
        timer.start()
        
    assert timer.start_time == 1000.0
    captured = capsys.readouterr()
    assert "[Process] Started tracking 50 iterations..." in captured.out

def test_timer_update_intervals(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that updates print only on designated intervals or at completion."""
    timer = LoopTimer(label="Loop", total_iterations=5, report_interval=2)
    
    with patch("time.time", side_effect=[1000.0, 1001.0, 1002.0, 1003.0, 1004.0, 1005.0]):
        timer.start()
        capsys.readouterr()  # Clear the start message from stdout buffer
        
        # Iteration 1: No print (1 % 2 != 0)
        timer.update(1)
        captured = capsys.readouterr()
        assert captured.out == ""
        
        # Iteration 2: Prints (2 % 2 == 0)
        timer.update(2)
        captured = capsys.readouterr()
        assert "[Loop] Progress: 2/5 (40.0%) | Elapsed: 2.00s" in captured.out
        
        # Iteration 5: Prints because it is the final iteration, catching the remainder
        timer.update(5)
        captured = capsys.readouterr()
        assert "[Loop] Progress: 5/5 (100.0%) | Elapsed: 5.00s" in captured.out

def test_timer_stop(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that stopping the timer computes and prints total time correctly."""
    timer = LoopTimer(label="EndToEnd", total_iterations=100, report_interval=10)
    
    with patch("time.time", side_effect=[1000.0, 1015.5]):
        timer.start()
        capsys.readouterr()  # Clear start message
        timer.stop()
        
    captured = capsys.readouterr()
    assert "[EndToEnd] Completed! Total Time: 15.50s" in captured.out

def test_unstarted_timer_raises_error() -> None:
    """Verify that calling update or stop before start raises a RuntimeError."""
    timer = LoopTimer(label="ErrorCheck", total_iterations=10, report_interval=2)
    
    with pytest.raises(RuntimeError, match="updated before start"):
        timer.update(1)
        
    with pytest.raises(RuntimeError, match="stopped before start"):
        timer.stop()

# ================= New Context Manager Tests =================

def test_context_manager_successful_flow(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify standard context manager setup, updates, and automatic breakdown."""
    # Side effects cover: 1. start(), 2. update(), 3. __exit__/stop()
    with patch("time.time", side_effect=[1000.0, 1004.0, 1010.0]):
        with LoopTimer(label="CtxMgr", total_iterations=10, report_interval=5) as timer:
            assert timer.start_time == 1000.0
            timer.update(5)
            
    captured = capsys.readouterr()
    # Confirm both startup message and intermediate update ran
    assert "[CtxMgr] Started tracking 10 iterations..." in captured.out
    assert "[CtxMgr] Progress: 5/10 (50.0%) | Elapsed: 4.00s" in captured.out
    # Confirm loop teardown automatically executed via __exit__
    assert "[CtxMgr] Completed! Total Time: 10.00s" in captured.out

def test_context_manager_exception_safety(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that the timer shuts down and records total time even if an error kills the loop."""
    with patch("time.time", side_effect=[1000.0, 1005.0]):
        with pytest.raises(ValueError, match="Simulated loop crash"):
            with LoopTimer(label="CrashTest", total_iterations=20, report_interval=5):
                raise ValueError("Simulated loop crash")
                
    captured = capsys.readouterr()
    # Ensure that despite the exception, __exit__ triggers stop() and tracks up to the failure point
    assert "[CrashTest] Completed! Total Time: 5.00s" in captured.out

