#!/usr/bin/env python3
"""
Quick Modbus TCP Connection Test
Just tests if we can connect and read some registers - no performance testing
"""

import yaml
from pymodbus.client import ModbusTcpClient

def load_config(config_file="config.yaml"):
    """Load configuration"""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def test_connection():
    """Test basic Modbus connection"""
    config = load_config()
    
    print("🚀 Quick Modbus TCP Connection Test")
    print("===================================")
    print(f"Host: {config['modbus']['host']}:{config['modbus']['port']}")
    print(f"Unit ID: {config['modbus']['unit_id']}")
    print(f"Timeout: {config['modbus']['timeout']}s")
    
    # Connect
    client = ModbusTcpClient(
        host=config['modbus']['host'],
        port=config['modbus']['port'],
        timeout=config['modbus']['timeout']
    )
    
    try:
        if not client.connect():
            print("❌ Failed to connect!")
            return False
            
        print("✅ Connected successfully!")
        
        # Test register reading
        start_addr = config['registers']['start_address']
        register_type = config['registers'].get('type', 'input')
        
        print(f"\n📍 Testing {register_type} registers starting at {start_addr}")
        
        # Convert address
        if register_type == 'input':
            if start_addr >= 30001:
                modbus_addr = start_addr - 30001
            else:
                modbus_addr = start_addr
        else:
            if start_addr >= 40001:
                modbus_addr = start_addr - 40001
            else:
                modbus_addr = start_addr
                
        print(f"   Modbus address: {modbus_addr}")
        
        # Test reads
        test_counts = [1, 5, 10, 20]
        for count in test_counts:
            try:
                if register_type == 'input':
                    response = client.read_input_registers(
                        address=modbus_addr,
                        count=count,
                        slave=config['modbus']['unit_id']
                    )
                else:
                    response = client.read_holding_registers(
                        address=modbus_addr,
                        count=count,
                        slave=config['modbus']['unit_id']
                    )
                
                if response.isError():
                    print(f"   ❌ Reading {count} registers: {response}")
                else:
                    print(f"   ✅ Reading {count} registers: OK")
                    print(f"      First few values: {response.registers[:min(3, len(response.registers))]}")
                    
            except Exception as e:
                print(f"   ❌ Reading {count} registers: {e}")
        
        print(f"\n🎯 Register meanings (from your register map):")
        print(f"   5001: nominal_output_power (watts)")
        print(f"   5003: daily_output_energy (kWh)")  
        print(f"   5008: inside_temperature (°C)")
        print(f"   5019: phase_a_voltage (volts)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    test_connection() 