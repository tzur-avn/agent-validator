# Progress Bar Feature

## Overview

The agent validator now includes beautiful progress bars that provide real-time visual feedback during agent execution. This makes it easy to track which agent is running and what step it's currently processing.

## Features

- **Visual Progress Tracking**: Each agent displays a progress bar showing:
  - Agent name
  - Current step being processed
  - Progress percentage
  - Time elapsed
  - Estimated time remaining

- **Multi-Agent Support**: When running multiple agents sequentially, each agent gets its own progress bar

- **Step-by-Step Visibility**: Progress bars show detailed steps:
  - **Spell Checker Agent**:
    1. Scraping web page
    2. Analyzing text with AI
    3. Generating report
  
  - **Visual QA Agent**:
    1. Capturing screenshot
    2. Analyzing visuals with AI
    3. Generating report

## How It Works

### Architecture

The progress tracking system consists of three main components:

1. **ProgressTracker** (`utils/progress_utils.py`): A utility class that manages Rich progress bars
2. **Base Agent** (`agents/base_agent.py`): Extended with progress callback support
3. **Orchestrator** (`core/orchestrator.py`): Manages progress tracker lifecycle and connects it to agents

### Progress Flow

```
Orchestrator creates ProgressTracker
    ↓
For each agent:
    ↓
    Start new progress task (agent name)
    ↓
    Set progress callback on agent
    ↓
    Agent calls _update_progress() at each step
    ↓
    Callback updates progress bar
    ↓
    Complete progress task when done
```

## Usage

### Default Behavior

Progress bars are **enabled by default** when running the validator:

```bash
pipenv run python main.py --url https://example.com
```

### Disable Progress Bars

Use the `--quiet` flag to suppress progress bars and most console output:

```bash
pipenv run python main.py --url https://example.com --quiet
```

This is useful for:
- Running in automated scripts
- Logging output to files
- CI/CD pipelines

## Implementation Details

### Adding Progress to New Agents

If you create a new agent, follow these steps to add progress tracking:

1. **Call `_update_progress()` in each workflow node**:
   ```python
   def my_node(self, state: MyState) -> Dict[str, Any]:
       """Process something."""
       self._update_progress("Doing something", advance=1)
       # ... do work ...
       return {"result": value}
   ```

2. **Set appropriate total steps** in orchestrator:
   ```python
   task_key = self.progress_tracker.start_task(
       agent_name=agent.name,
       description="Processing",
       total=3,  # Number of workflow nodes
   )
   ```

### Progress Callback Signature

```python
def progress_callback(step_name: str, advance: int = 1) -> None:
    """
    Called by agent to report progress.
    
    Args:
        step_name: Human-readable name of current step
        advance: Amount to advance progress (default: 1)
    """
```

## Technical Stack

- **[Rich](https://rich.readthedocs.io/)**: Python library for rich text and beautiful formatting in the terminal
- Components used:
  - `Progress`: Main progress tracking class
  - `SpinnerColumn`: Animated spinner
  - `BarColumn`: Visual progress bar
  - `TaskProgressColumn`: Percentage display
  - `TimeElapsedColumn`: Time elapsed
  - `TimeRemainingColumn`: Estimated time remaining

## Benefits

1. **User Experience**: Users can see exactly what's happening and how long it might take
2. **Debugging**: Easy to identify which step is slow or stuck
3. **Professional**: Modern, colorful console output that looks polished
4. **Non-Intrusive**: Automatically disabled in quiet mode or when piping output

## Examples

### Sequential Execution
When running agents sequentially, each agent's progress bar appears one after another:

```
⠋ [SpellChecker] Scraping web page      ━━━━━━━━━╺━━━━━━━━━━━  33% 0:00:02 0:00:04
⠴ [VisualQA] Capturing screenshot       ━━━━━━━━━━━━━━━━━━━━━   0% 0:00:00 -:--:--
```

### Parallel Execution
When running in parallel mode (with `--parallel`), multiple progress bars may update simultaneously.

## Configuration

No additional configuration is needed. The progress tracker:
- Automatically detects quiet mode
- Adjusts to terminal capabilities
- Handles errors gracefully
- Cleans up resources properly

## Future Enhancements

Potential improvements for the future:
- Granular progress within AI analysis steps
- Progress for file I/O operations
- Custom themes/colors
- Progress persistence across runs
- Integration with web UI (if developed)
