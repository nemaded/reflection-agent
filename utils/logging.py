from colorama import Fore, Style
import time

def fancy_step_tracker(current_step: int, total_steps: int) -> None:
    """
    Displays a fancy progress tracker for the current step.
    
    Args:
        current_step (int): The current step number (0-based)
        total_steps (int): The total number of steps
    """
    # Calculate progress percentage
    progress = (current_step + 1) / total_steps * 100
    
    # Create the progress bar
    bar_length = 30
    filled_length = int(bar_length * (current_step + 1) / total_steps)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    # Print the progress bar with colors
    print(f"\n{Fore.CYAN}Step {current_step + 1}/{total_steps} {Style.BRIGHT}[{bar}] {progress:.1f}%{Style.RESET_ALL}")
    
    # Add a small delay for visual effect
    time.sleep(0.1) 