#!/usr/bin/env python3
"""
Quick test runner for Modbus TCP Performance Tester
Uses the shortened configuration for faster testing
"""

from modbus_tester import ModbusTester

def main():
    print("Quick Modbus TCP Performance Test")
    print("=================================")
    print("Running with shortened test duration...")
    
    try:
        tester = ModbusTester("config_quick.yaml")
        tester.run_all_tests()
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 