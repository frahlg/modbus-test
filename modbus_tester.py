#!/usr/bin/env python3
"""
Modbus TCP Performance Testing Tool

This tool tests Modbus TCP communication with various frequencies and register counts,
collecting detailed statistics on latency, dropouts, and overall performance.
"""

import time
import yaml
import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from statistics import mean, median, stdev
import pandas as pd
from tabulate import tabulate

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException, ConnectionException


@dataclass
class TestResult:
    """Single test measurement result"""
    timestamp: float
    latency_ms: float
    success: bool
    error_message: Optional[str] = None
    register_count: int = 0
    frequency_hz: float = 0


@dataclass  
class TestStats:
    """Statistics for a test run"""
    frequency_hz: float
    register_count: int
    duration_minutes: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    avg_latency_ms: float
    median_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    latency_std_ms: float
    dropout_count: int
    max_consecutive_failures: int


class ModbusTester:
    """Main Modbus testing class"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config = self.load_config(config_file)
        self.client = None
        self.results: List[TestResult] = []
        self.setup_logging()
        self.setup_output_directory()
        
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Config file {config_file} not found!")
            raise
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            raise
            
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('modbus_test.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_output_directory(self):
        """Create output directory if it doesn't exist"""
        output_dir = Path(self.config['output']['output_directory'])
        output_dir.mkdir(exist_ok=True)
        
    def connect(self) -> bool:
        """Establish connection to Modbus server"""
        try:
            self.client = ModbusTcpClient(
                host=self.config['modbus']['host'],
                port=self.config['modbus']['port'],
                timeout=self.config['modbus']['timeout']
            )
            
            if self.client.connect():
                self.logger.info(f"✓ Connected to Modbus server at {self.config['modbus']['host']}:{self.config['modbus']['port']}")
                
                # Test connection with a simple read
                return self.test_connection()
            else:
                self.logger.error("✗ Failed to connect to Modbus server")
                return False
                
        except Exception as e:
            self.logger.error(f"✗ Connection error: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test the connection by trying to read a few registers"""
        print(f"\n🔍 Testing connection by reading registers...")
        
        start_addr = self.config['registers']['start_address']
        register_type = self.config['registers'].get('type', 'input')  # Default to input registers
        
        # Convert address for different register types
        if register_type == 'input':
            # Input registers (30001-39999 -> 0-based)
            if start_addr >= 30001:
                modbus_addr = start_addr - 30001
            else:
                modbus_addr = start_addr
            print(f"📍 Testing INPUT registers starting at {start_addr} (Modbus address {modbus_addr})")
        else:
            # Holding registers (40001-49999 -> 0-based)  
            if start_addr >= 40001:
                modbus_addr = start_addr - 40001
            else:
                modbus_addr = start_addr
            print(f"📍 Testing HOLDING registers starting at {start_addr} (Modbus address {modbus_addr})")
        
        try:
            # Try to read 1 register first
            start_time = time.perf_counter()
            
            if register_type == 'input':
                response = self.client.read_input_registers(
                    address=modbus_addr,
                    count=1,
                    slave=self.config['modbus']['unit_id']
                )
            else:
                response = self.client.read_holding_registers(
                    address=modbus_addr,
                    count=1,
                    slave=self.config['modbus']['unit_id']
                )
            
            end_time = time.perf_counter()
            latency = (end_time - start_time) * 1000
            
            if response.isError():
                print(f"❌ Test read failed: {response}")
                self.logger.error(f"Test read failed: {response}")
                return False
            else:
                print(f"✅ Test read successful!")
                print(f"   - Register {start_addr}: {response.registers[0]}")
                print(f"   - Latency: {latency:.2f}ms")
                print(f"   - Unit ID: {self.config['modbus']['unit_id']}")
                
                # Try reading a few more to test different counts
                for count in [5, 10]:
                    try:
                        if register_type == 'input':
                            response = self.client.read_input_registers(
                                address=modbus_addr,
                                count=count,
                                slave=self.config['modbus']['unit_id']
                            )
                        else:
                            response = self.client.read_holding_registers(
                                address=modbus_addr,
                                count=count,
                                slave=self.config['modbus']['unit_id']
                            )
                        
                        if response.isError():
                            print(f"⚠️  Reading {count} registers failed: {response}")
                        else:
                            print(f"✅ Reading {count} registers: OK (first value: {response.registers[0]})")
                    except Exception as e:
                        print(f"⚠️  Reading {count} registers failed: {e}")
                        
                return True
                
        except Exception as e:
            print(f"❌ Test read exception: {e}")
            self.logger.error(f"Test read exception: {e}")
            return False
            
    def disconnect(self):
        """Close Modbus connection"""
        if self.client:
            self.client.close()
            self.logger.info("Disconnected from Modbus server")
            
    def read_registers(self, count: int) -> TestResult:
        """Read registers and measure performance"""
        start_time = time.perf_counter()
        timestamp = time.time()
        
        try:
            start_addr = self.config['registers']['start_address']
            register_type = self.config['registers'].get('type', 'input')  # Default to input registers
            
            # Convert address for different register types
            if register_type == 'input':
                if start_addr >= 30001:
                    modbus_addr = start_addr - 30001
                else:
                    modbus_addr = start_addr
                    
                response = self.client.read_input_registers(
                    address=modbus_addr,
                    count=count,
                    slave=self.config['modbus']['unit_id']
                )
            else:
                if start_addr >= 40001:
                    modbus_addr = start_addr - 40001
                else:
                    modbus_addr = start_addr
                    
                response = self.client.read_holding_registers(
                    address=modbus_addr,
                    count=count,
                    slave=self.config['modbus']['unit_id']
                )
            
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            
            if response.isError():
                return TestResult(
                    timestamp=timestamp,
                    latency_ms=latency_ms,
                    success=False,
                    error_message=str(response),
                    register_count=count
                )
            else:
                return TestResult(
                    timestamp=timestamp,
                    latency_ms=latency_ms,
                    success=True,
                    register_count=count
                )
                
        except Exception as e:
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            
            return TestResult(
                timestamp=timestamp,
                latency_ms=latency_ms,
                success=False,
                error_message=str(e),
                register_count=count
            )
            
    def run_test(self, frequency_hz: float, register_count: int, duration_minutes: float) -> List[TestResult]:
        """Run a single test with specified parameters"""
        results = []
        interval = 1.0 / frequency_hz
        end_time = time.time() + (duration_minutes * 60)
        
        self.logger.info(f"Starting test: {frequency_hz}Hz, {register_count} registers, {duration_minutes} minutes")
        print(f"⏱️  Running for {duration_minutes} minute(s) at {frequency_hz}Hz...")
        
        request_count = 0
        success_count = 0
        failure_count = 0
        next_request_time = time.time()
        
        # Show first few results for immediate feedback
        show_details = True
        detail_count = 0
        
        while time.time() < end_time:
            current_time = time.time()
            
            if current_time >= next_request_time:
                result = self.read_registers(register_count)
                result.frequency_hz = frequency_hz
                results.append(result)
                request_count += 1
                
                if result.success:
                    success_count += 1
                else:
                    failure_count += 1
                    
                # Show first few results in detail
                if show_details and detail_count < 5:
                    if result.success:
                        print(f"   ✅ Request {request_count}: {result.latency_ms:.2f}ms")
                    else:
                        print(f"   ❌ Request {request_count}: FAILED - {result.error_message}")
                    detail_count += 1
                    if detail_count >= 5:
                        print(f"   ... (continuing silently, will show summary)")
                        show_details = False
                
                # Schedule next request
                next_request_time += interval
                
                # If we're falling behind, catch up but don't spam
                if next_request_time < current_time:
                    next_request_time = current_time + interval
                    
            else:
                # Sleep until next request time
                sleep_time = next_request_time - current_time
                if sleep_time > 0:
                    time.sleep(min(sleep_time, 0.01))  # Max sleep of 10ms
                    
        print(f"📊 Completed: {success_count}/{request_count} successful ({success_count/request_count*100:.1f}%)")
        self.logger.info(f"Test completed: {request_count} requests sent, {success_count} successful")
        return results
        
    def calculate_stats(self, results: List[TestResult]) -> TestStats:
        """Calculate statistics from test results"""
        if not results:
            return None
            
        successful_results = [r for r in results if r.success]
        latencies = [r.latency_ms for r in successful_results]
        
        # Calculate consecutive failures
        max_consecutive_failures = 0
        current_consecutive_failures = 0
        
        for result in results:
            if not result.success:
                current_consecutive_failures += 1
                max_consecutive_failures = max(max_consecutive_failures, current_consecutive_failures)
            else:
                current_consecutive_failures = 0
                
        # Calculate dropout count (consecutive failures > 1)
        dropout_count = 0
        in_dropout = False
        consecutive_failures = 0
        
        for result in results:
            if not result.success:
                consecutive_failures += 1
                if consecutive_failures >= 2 and not in_dropout:
                    dropout_count += 1
                    in_dropout = True
            else:
                consecutive_failures = 0
                in_dropout = False
        
        return TestStats(
            frequency_hz=results[0].frequency_hz,
            register_count=results[0].register_count,
            duration_minutes=self.config['test']['duration_minutes'],
            total_requests=len(results),
            successful_requests=len(successful_results),
            failed_requests=len(results) - len(successful_results),  
            success_rate=len(successful_results) / len(results) * 100 if results else 0,
            avg_latency_ms=mean(latencies) if latencies else 0,
            median_latency_ms=median(latencies) if latencies else 0,
            min_latency_ms=min(latencies) if latencies else 0,
            max_latency_ms=max(latencies) if latencies else 0,
            latency_std_ms=stdev(latencies) if len(latencies) > 1 else 0,
            dropout_count=dropout_count,
            max_consecutive_failures=max_consecutive_failures
        )
        
    def save_results(self, all_stats: List[TestStats], all_results: List[TestResult]):
        """Save test results and statistics"""
        output_dir = Path(self.config['output']['output_directory'])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save summary statistics
        if self.config['output']['save_summary_stats']:
            stats_data = [asdict(stats) for stats in all_stats]
            stats_df = pd.DataFrame(stats_data)
            
            # Save as CSV
            stats_file = output_dir / f'test_stats_{timestamp}.csv'
            stats_df.to_csv(stats_file, index=False)
            
            # Save as JSON
            stats_json_file = output_dir / f'test_stats_{timestamp}.json'
            with open(stats_json_file, 'w') as f:
                json.dump(stats_data, f, indent=2)
                
            self.logger.info(f"Statistics saved to {stats_file} and {stats_json_file}")
            
        # Save detailed logs
        if self.config['output']['save_detailed_logs']:
            results_data = [asdict(result) for result in all_results]
            results_df = pd.DataFrame(results_data)
            
            results_file = output_dir / f'detailed_results_{timestamp}.csv'
            results_df.to_csv(results_file, index=False)
            
            self.logger.info(f"Detailed results saved to {results_file}")
            
    def print_summary(self, all_stats: List[TestStats]):
        """Print a summary table of all test results"""
        print("\n" + "="*80)
        print("MODBUS TCP PERFORMANCE TEST SUMMARY")
        print("="*80)
        
        # Prepare data for table
        table_data = []
        for stats in all_stats:
            table_data.append([
                f"{stats.frequency_hz:.1f}",
                f"{stats.register_count}",
                f"{stats.success_rate:.1f}%",
                f"{stats.avg_latency_ms:.2f}",
                f"{stats.median_latency_ms:.2f}",
                f"{stats.max_latency_ms:.2f}",
                f"{stats.dropout_count}",
                f"{stats.max_consecutive_failures}"
            ])
            
        headers = [
            "Freq (Hz)", "Registers", "Success %", "Avg Lat (ms)", 
            "Med Lat (ms)", "Max Lat (ms)", "Dropouts", "Max Fails"
        ]
        
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        print()
        
    def run_all_tests(self):
        """Run all configured tests"""
        if not self.connect():
            return
            
        all_stats = []
        all_results = []
        
        try:
            frequencies = self.config['test']['frequencies']
            register_counts = self.config['test']['register_counts']
            duration = self.config['test']['duration_minutes']
            
            total_tests = len(frequencies) * len(register_counts)
            current_test = 0
            
            for frequency in frequencies:
                for register_count in register_counts:
                    current_test += 1
                    print(f"\n{'='*60}")
                    print(f"🧪 Test {current_test}/{total_tests}: {frequency}Hz, {register_count} registers")
                    print(f"{'='*60}")
                    
                    results = self.run_test(frequency, register_count, duration)
                    stats = self.calculate_stats(results)
                    
                    if stats:
                        all_stats.append(stats)
                        all_results.extend(results)
                        
                        # Print immediate results
                        print(f"📈 Results:")
                        print(f"   Success rate: {stats.success_rate:.1f}%")
                        print(f"   Avg latency: {stats.avg_latency_ms:.2f}ms")
                        print(f"   Dropouts: {stats.dropout_count}")
                        
            # Save and display results
            self.save_results(all_stats, all_results)  
            self.print_summary(all_stats)
            
        except KeyboardInterrupt:
            self.logger.info("Test interrupted by user")
        finally:
            self.disconnect()


def main():
    """Main entry point"""
    import sys
    
    print("🚀 Modbus TCP Performance Tester")
    print("=============================")
    
    # Check for config file argument
    config_file = "config.yaml"
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
        print(f"Using config file: {config_file}")
    
    try:
        tester = ModbusTester(config_file)
        tester.run_all_tests()
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 