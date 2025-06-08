#!/bin/bash
# Example usage for Modbus TCP Performance Tester

echo "Modbus TCP Performance Tester - Usage Examples"
echo "==============================================="
echo ""

echo "1. Run with default config (5 minutes per test):"
echo "   python3 modbus_tester.py"
echo ""

echo "2. Run with custom config file:"
echo "   python3 modbus_tester.py config_quick.yaml"
echo ""

echo "3. Run quick test (1 minute per test):"
echo "   python3 run_quick_test.py"
echo ""

echo "4. Run via main.py:"
echo "   python3 main.py"
echo ""

echo "Before running, make sure to:"
echo "1. Edit config.yaml and set your inverter's IP address"
echo "2. Verify your inverter accepts Modbus TCP connections on port 502"
echo "3. Check that the register addresses are correct for your device"
echo ""

echo "Available configuration files:"
echo "- config.yaml: Full test suite (5 minutes per test)"
echo "- config_quick.yaml: Quick test suite (1 minute per test)"
echo ""

echo "Results will be saved in the 'test_results/' directory" 