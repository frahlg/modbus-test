# Modbus TCP Performance Tester

A simple tool to test Modbus TCP communication performance with various frequencies and register counts, collecting detailed statistics on latency, dropouts, and overall performance.

## Features

- Test different polling frequencies (1Hz, 2Hz, 5Hz, 10Hz, etc.)
- Test different numbers of registers (1, 10, 20, 50, 100, etc.)
- Measure latency statistics (avg, median, min, max, std deviation)
- Detect and count dropouts (consecutive failures)
- Track success rates and connection reliability
- Export results to CSV and JSON formats
- Real-time progress reporting

## Quick Start

1. **Setup environment with uv:**
   ```bash
   # Install uv if you don't have it
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Create virtual environment and install dependencies
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install "pymodbus[tcp]>=3.0.0" pyyaml pandas tabulate
   ```

2. **Configure your inverter settings:**
   Edit `config.yaml` and set your inverter's IP address:
   ```yaml
   modbus:
     host: "192.168.1.100"  # Change to your inverter's IP
     port: 502
     unit_id: 1
   ```

3. **Run the test:**
   ```bash
   python main.py
   ```
   or
   ```bash
   python modbus_tester.py
   ```

## Configuration

The `config.yaml` file contains all test parameters:

### Modbus Settings
- `host`: IP address of your Modbus TCP server (inverter)
- `port`: Modbus TCP port (usually 502)
- `unit_id`: Modbus slave/unit ID (usually 1)
- `timeout`: Connection timeout in seconds

### Test Parameters
- `duration_minutes`: How long to run each test combination
- `frequencies`: List of polling frequencies to test (Hz)
- `register_counts`: List of register counts to test per request

### Register Settings
- `start_address`: Starting Modbus register address (e.g., 40001)

### Output Settings
- `save_detailed_logs`: Save individual request results
- `save_summary_stats`: Save aggregated statistics
- `output_directory`: Directory for result files

## Example Test Run

The tool will run all combinations of frequencies and register counts. For example, with default settings:

```
Running test 1/20: 1Hz, 1 registers
  Success rate: 100.0%
  Avg latency: 15.23ms
  Dropouts: 0

Running test 2/20: 1Hz, 10 registers
  Success rate: 100.0%
  Avg latency: 18.45ms
  Dropouts: 0

...
```

## Results

After completion, you'll see a summary table:

```
================================================================================
MODBUS TCP PERFORMANCE TEST SUMMARY
================================================================================
┌───────────┬───────────┬───────────┬─────────────┬─────────────┬─────────────┬───────────┬───────────┐
│ Freq (Hz) │ Registers │ Success % │ Avg Lat (ms)│ Med Lat (ms)│ Max Lat (ms)│ Dropouts  │ Max Fails │
├───────────┼───────────┼───────────┼─────────────┼─────────────┼─────────────┼───────────┼───────────┤
│ 1.0       │ 1         │ 100.0%    │ 15.23       │ 14.82       │ 45.12       │ 0         │ 0         │
│ 1.0       │ 10        │ 100.0%    │ 18.45       │ 17.91       │ 52.33       │ 0         │ 0         │
│ 2.0       │ 1         │ 99.8%     │ 16.11       │ 15.44       │ 128.77      │ 1         │ 2         │
└───────────┴───────────┴───────────┴─────────────┴─────────────┴─────────────┴───────────┴───────────┘
```

## Output Files

Results are saved in the `test_results/` directory:

- `test_stats_YYYYMMDD_HHMMSS.csv`: Summary statistics
- `test_stats_YYYYMMDD_HHMMSS.json`: Summary statistics in JSON format
- `detailed_results_YYYYMMDD_HHMMSS.csv`: Individual request results
- `modbus_test.log`: Detailed log file

## Statistics Explained

- **Success Rate**: Percentage of successful requests
- **Latency**: Time from request start to response completion
- **Dropouts**: Number of times there were 2+ consecutive failures
- **Max Fails**: Maximum number of consecutive failures

## Customization

You can easily modify the test parameters in `config.yaml`:

```yaml
test:
  duration_minutes: 2  # Shorter tests
  frequencies: [1, 5, 10, 20]  # Add higher frequencies
  register_counts: [1, 5, 25, 50, 100]  # Different register patterns
```

## Troubleshooting

1. **Connection issues**: Check IP address, port, and network connectivity
2. **Permission errors**: Ensure the inverter allows Modbus TCP connections
3. **Timeout errors**: Increase timeout value in config
4. **High latency**: Check network conditions and inverter load

## Requirements

- Python 3.9+
- uv (fast Python package installer)
- pymodbus 3.0+
- pandas
- pyyaml
- tabulate

Dependencies are installed via `uv pip install` as shown in the Quick Start section.
