#!/usr/bin/env python3
"""
Modbus TCP Performance Testing Tool
Entry point script
"""

from modbus_tester import main as run_modbus_test


def main():
    """Main entry point"""
    print("Starting Modbus TCP Performance Test...")
    return run_modbus_test()


if __name__ == "__main__":
    exit(main())
