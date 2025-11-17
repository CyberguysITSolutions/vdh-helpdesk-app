#!/usr/bin/env python3
"""
Test script for public forms implementation.
Tests the public_forms module functions in MOCK_DATA mode.
"""
import os
import sys

# Enable MOCK_DATA mode
os.environ["MOCK_DATA"] = "1"

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        import public_forms
        print("  ✓ public_forms imported successfully")
        
        # Check that functions exist
        assert hasattr(public_forms, 'render_public_ticket_form')
        assert hasattr(public_forms, 'render_public_vehicle_request_form')
        assert hasattr(public_forms, 'render_public_procurement_form')
        assert hasattr(public_forms, 'insert_and_get_id')
        assert hasattr(public_forms, 'execute_non_query')
        assert hasattr(public_forms, 'get_mock_data_mode')
        print("  ✓ All required functions exist")
        
        return public_forms
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return None

def test_mock_data_mode(public_forms):
    """Test MOCK_DATA mode detection."""
    print("\nTesting MOCK_DATA mode...")
    mode = public_forms.get_mock_data_mode()
    if mode:
        print("  ✓ MOCK_DATA mode is enabled")
    else:
        print("  ✗ MOCK_DATA mode is not enabled")
    return mode

def test_insert_and_get_id(public_forms):
    """Test insert_and_get_id in MOCK_DATA mode."""
    print("\nTesting insert_and_get_id...")
    query = "INSERT INTO dbo.Tickets (name) VALUES (?)"
    params = ("Test User",)
    
    new_id, error = public_forms.insert_and_get_id(query, params)
    
    if error:
        print(f"  ✗ Error: {error}")
        return False
    elif new_id and isinstance(new_id, int):
        print(f"  ✓ Returned mock ID: {new_id}")
        return True
    else:
        print(f"  ✗ Unexpected result: {new_id}")
        return False

def test_execute_non_query(public_forms):
    """Test execute_non_query in MOCK_DATA mode."""
    print("\nTesting execute_non_query...")
    query = "UPDATE dbo.Tickets SET status='New' WHERE id=?"
    params = (1,)
    
    success, error = public_forms.execute_non_query(query, params)
    
    if error:
        print(f"  ✗ Error: {error}")
        return False
    elif success:
        print(f"  ✓ Mock execution successful")
        return True
    else:
        print(f"  ✗ Unexpected result: success={success}")
        return False

def test_syntax():
    """Test that main app file has valid syntax."""
    print("\nTesting helpdesk_app.py syntax...")
    try:
        import py_compile
        py_compile.compile('helpdesk_app.py', doraise=True)
        print("  ✓ helpdesk_app.py syntax is valid")
        return True
    except py_compile.PyCompileError as e:
        print(f"  ✗ Syntax error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Public Forms Implementation Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test imports
    public_forms = test_imports()
    results.append(public_forms is not None)
    
    if public_forms:
        # Test MOCK_DATA mode
        results.append(test_mock_data_mode(public_forms))
        
        # Test helper functions
        results.append(test_insert_and_get_id(public_forms))
        results.append(test_execute_non_query(public_forms))
    
    # Test main app syntax
    results.append(test_syntax())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
