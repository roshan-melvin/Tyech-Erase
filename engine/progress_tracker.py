#!/usr/bin/env python3
"""
Progress tracking and display for Tyech Secure Eraser operations.
"""

import time
import threading
import sys


class ProgressTracker:
    """Track and display erase progress with time estimation."""
    
    def __init__(self):
        self.current_progress = 0
        self.current_stage = ""
        self.total_stages = 1
        self.current_stage_num = 0
        self.is_running = False
        self._progress_thread = None
        self.start_time = None
        self.last_update_time = None
        self.progress_history = []
    
    def start_progress(self, total_stages=1, stage_name="Erasing"):
        """Start progress tracking."""
        self.total_stages = total_stages
        self.current_stage_num = 0
        self.current_stage = stage_name
        self.current_progress = 0
        self.is_running = True
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.progress_history = []
        
        # Start progress display thread
        self._progress_thread = threading.Thread(target=self._display_progress)
        self._progress_thread.daemon = True
        self._progress_thread.start()
    
    def update_stage(self, stage_num, stage_name, progress=0):
        """Update current stage information."""
        self.current_stage_num = stage_num
        self.current_stage = stage_name
        self.current_progress = progress
        
        # Add a progress history entry for stage transition
        current_time = time.time()
        overall_progress = self._calculate_overall_progress()
        
        # Store progress history for time estimation
        if len(self.progress_history) > 20:
            self.progress_history.pop(0)
        
        self.progress_history.append({
            'time': current_time,
            'progress': self.current_progress,
            'overall_progress': overall_progress
        })
        
        self.last_update_time = current_time
    
    def update_progress(self, progress):
        """Update progress within current stage."""
        self.current_progress = min(100, max(0, progress))
        current_time = time.time()
        
        # Store progress history for time estimation
        if len(self.progress_history) > 20:
            self.progress_history.pop(0)
        
        self.progress_history.append({
            'time': current_time,
            'progress': self.current_progress,
            'overall_progress': self._calculate_overall_progress()
        })
        
        self.last_update_time = current_time
    
    def stop_progress(self):
        """Stop progress tracking."""
        self.is_running = False
        if self._progress_thread:
            self._progress_thread.join(timeout=1.0)
        # Clear the progress line
        print("\r" + " " * 120 + "\r", end="", flush=True)
    
    def _calculate_overall_progress(self):
        """Calculate overall progress across all stages."""
        stage_weight = 100 / self.total_stages
        overall_progress = (self.current_stage_num * stage_weight) + (self.current_progress * stage_weight / 100)
        return min(100, overall_progress)
    
    def _estimate_time_remaining(self):
        """Estimate time remaining based on progress history."""
        if len(self.progress_history) < 2:
            return None
            
        overall_progress = self._calculate_overall_progress()
        if overall_progress <= 0:
            return None
            
        # Use recent progress points to estimate speed
        recent_history = self.progress_history[-5:]  # Last 5 updates for faster response
        if len(recent_history) < 2:
            return None
            
        time_diff = recent_history[-1]['time'] - recent_history[0]['time']
        progress_diff = recent_history[-1]['overall_progress'] - recent_history[0]['overall_progress']
        
        # Handle stage transitions and very small progress changes
        if time_diff <= 0:
            return None
        
        # If progress is stuck or moving backward (stage transition), use overall average
        if progress_diff <= 0.1:
            time_diff = time.time() - self.start_time
            progress_diff = overall_progress
            
        # Calculate speed (progress per second)
        speed = progress_diff / time_diff
        remaining_progress = 100 - overall_progress
        
        if speed > 0:
            return remaining_progress / speed
        return None
    
    def _format_time(self, seconds):
        """Format seconds into human readable time."""
        if seconds is None:
            return "Unknown"
            
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def _display_progress(self):
        """Display progress with time estimation in a separate thread."""
        while self.is_running:
            overall_progress = self._calculate_overall_progress()
            eta = self._estimate_time_remaining()
            eta_str = self._format_time(eta)
            
            # Create progress bar
            bar_width = 30
            filled = int((overall_progress / 100) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            
            # Display progress line
            stage_info = f"Stage {self.current_stage_num + 1}/{self.total_stages}: {self.current_stage}"
            progress_line = f"\r🔄 {stage_info} [{bar}] {overall_progress:.1f}% | ETA: {eta_str}"
            print(progress_line[:120], end="", flush=True)
            
            time.sleep(0.5)
