#!/usr/bin/env python3
"""
Code syntax checker and fixer for servo controller project
Supports both Python and Bash scripts
"""

import os
import sys
import subprocess
import re
import tempfile
import argparse
from pathlib import Path

def check_python_syntax(file_path):
    """Check Python file for syntax errors using pyflakes and pylint"""
    print(f"\n🔍 Checking Python syntax: {file_path}")
    
    # Use py_compile to check for syntax errors
    compile_result = subprocess.run(
        [sys.executable, "-m", "py_compile", file_path],
        capture_output=True, text=True
    )
    
    if compile_result.returncode != 0:
        print("❌ Python syntax errors found:")
        print(compile_result.stderr)
        return False
    
    # Try to run pyflakes if available
    try:
        pyflakes_result = subprocess.run(
            ["pyflakes", file_path],
            capture_output=True, text=True
        )
        
        if pyflakes_result.stdout or pyflakes_result.stderr:
            print("⚠️ Pyflakes warnings:")
            print(pyflakes_result.stdout or pyflakes_result.stderr)
        else:
            print("✅ No pyflakes issues found")
    except FileNotFoundError:
        print("⚠️ pyflakes not installed. Install with: pip install pyflakes")
    
    print("✅ No Python syntax errors found")
    return True

def fix_python_syntax(file_path):
    """Try to fix common Python syntax issues"""
    print(f"\n🔧 Fixing Python syntax: {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix common issues
    fixed_content = content
    
    # Fix missing colons after function/class definitions
    fixed_content = re.sub(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*$', 
                          r'def \1():', fixed_content, flags=re.MULTILINE)
    
    # Fix indentation (simple cases only)
    lines = fixed_content.split('\n')
    fixed_lines = []
    in_block = False
    for line in lines:
        if re.match(r'^(def|class|if|while|for|try|except|finally|else|elif)\s', line) and line.rstrip().endswith(':'):
            in_block = True
            fixed_lines.append(line)
        elif in_block and line.strip() and not line.startswith(' '):
            fixed_lines.append('    ' + line)
        else:
            fixed_lines.append(line)
    
    fixed_content = '\n'.join(fixed_lines)
    
    # Fix missing parentheses in print
    fixed_content = re.sub(r'print\s+([^(].*?)$', r'print(\1)', fixed_content, flags=re.MULTILINE)
    
    # Write back the fixed content if changes were made
    if fixed_content != content:
        with open(file_path, 'w') as f:
            f.write(fixed_content)
        print("✅ Fixed common Python syntax issues")
    else:
        print("✅ No syntax issues to fix")
    
    return True

def check_bash_syntax(file_path):
    """Check Bash script for syntax errors using shellcheck"""
    print(f"\n🔍 Checking Bash syntax: {file_path}")
    
    # First use bash -n to check syntax
    bash_check = subprocess.run(
        ["bash", "-n", file_path],
        capture_output=True, text=True
    )
    
    if bash_check.returncode != 0:
        print("❌ Bash syntax errors found:")
        print(bash_check.stderr)
        return False
    
    # Try to run shellcheck if available
    try:
        shellcheck_result = subprocess.run(
            ["shellcheck", "-x", file_path],
            capture_output=True, text=True
        )
        
        if shellcheck_result.returncode != 0:
            print("⚠️ Shellcheck warnings:")
            print(shellcheck_result.stdout or shellcheck_result.stderr)
        else:
            print("✅ No shellcheck issues found")
    except FileNotFoundError:
        print("⚠️ shellcheck not installed. Install with: apt install shellcheck")
    
    print("✅ No Bash syntax errors found")
    return True

def fix_bash_syntax(file_path):
    """Try to fix common Bash syntax issues"""
    print(f"\n🔧 Fixing Bash syntax: {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix common issues
    fixed_content = content
    
    # Fix shebang line if missing
    if not fixed_content.startswith('#!/'):
        fixed_content = '#!/bin/bash\n' + fixed_content
    
    # Fix missing execute permission
    os.chmod(file_path, 0o755)
    
    # Fix function definitions
    fixed_content = re.sub(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*{', 
                          r'\1() {', fixed_content)
    
    # Fix if statements without then
    fixed_content = re.sub(r'if\s+\[.*\]\s*$', 
                          r'\g<0>\nthen', fixed_content, flags=re.MULTILINE)
    
    # Write back the fixed content if changes were made
    if fixed_content != content:
        with open(file_path, 'w') as f:
            f.write(fixed_content)
        print("✅ Fixed common Bash syntax issues")
    else:
        print("✅ No syntax issues to fix")
    
    return True

def check_ps3_controller_mappings(file_path):
    """Check for correct PS3 controller button mappings"""
    if not file_path.endswith('.py'):
        return True
    
    print(f"\n🎮 Checking PS3 controller mappings: {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Look for PS3 button mappings
    if 'PS3_BUTTON_MAPPINGS' in content:
        # Check for critical mappings
        required_buttons = [
            '304: "Cross', '305: "Circle', 
            '307: "Triangle', '308: "Square'
        ]
        
        missing = [btn for btn in required_buttons if btn not in content]
        
        if missing:
            print("❌ Missing PS3 button mappings:")
            for btn in missing:
                print(f"  - {btn}")
            
            # Attempt to fix mappings
            mappings_pattern = r'PS3_BUTTON_MAPPINGS = \{[^}]+\}'
            correct_mappings = """PS3_BUTTON_MAPPINGS = {
    304: "Cross (✕)",      # South 
    305: "Circle (○)",     # East
    307: "Triangle (△)",   # North
    308: "Square (□)",     # West
    294: "L1",             # Left shoulder
    295: "R1",             # Right shoulder
    298: "L2",             # Left trigger
    299: "R2",             # Right trigger
    300: "D-Pad Up",
    301: "D-Pad Right",
    302: "D-Pad Down",
    303: "D-Pad Left",
    288: "Select",
    291: "Start",
    292: "PS Button",
    296: "L3",             # Left stick press
    297: "R3",             # Right stick press
    289: "Unknown (289)",  # Additional buttons
    290: "Unknown (290)",  # Additional buttons
    293: "Unknown (293)"   # Additional buttons
}"""
            
            fixed_content = re.sub(mappings_pattern, correct_mappings, content)
            
            if fixed_content != content:
                with open(file_path, 'w') as f:
                    f.write(fixed_content)
                print("✅ Fixed PS3 button mappings")
                return True
            
            return False
        else:
            print("✅ PS3 button mappings look correct")
    
    return True

def scan_directory(directory, fix=False):
    """Scan directory for Python and Bash files and check syntax"""
    print(f"Scanning directory: {directory}")
    
    success = True
    
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            
            if file.endswith('.py'):
                if fix:
                    fix_python_syntax(file_path)
                    check_ps3_controller_mappings(file_path)
                success &= check_python_syntax(file_path)
            
            elif file.endswith('.sh') or os.access(file_path, os.X_OK):
                try:
                    # Check if file is a bash script
                    with open(file_path, 'r') as f:
                        first_line = f.readline().strip()
                    
                    if 'bash' in first_line or 'sh' in first_line:
                        if fix:
                            fix_bash_syntax(file_path)
                        success &= check_bash_syntax(file_path)
                except (UnicodeDecodeError, IsADirectoryError):
                    # Skip binary files or directories
                    pass
    
    return success

def get_recommended_fixes(file_path):
    """Generate recommended fixes for the file"""
    if file_path.endswith('.py'):
        try:
            # Try to use autopep8 if available
            result = subprocess.run(
                ["autopep8", "--diff", file_path],
                capture_output=True, text=True
            )
            
            if result.stdout:
                print("\n📝 Recommended Python fixes:")
                print(result.stdout)
                
                if input("Apply these fixes? (y/n): ").lower() == 'y':
                    subprocess.run(["autopep8", "--in-place", file_path])
                    print("✅ Applied autopep8 fixes")
        except FileNotFoundError:
            print("⚠️ autopep8 not installed. Install with: pip install autopep8")
    
    elif file_path.endswith('.sh') or os.access(file_path, os.X_OK):
        try:
            # Try to use shfmt if available
            result = subprocess.run(
                ["shfmt", "-d", file_path],
                capture_output=True, text=True
            )
            
            if result.stdout:
                print("\n📝 Recommended Bash fixes:")
                print(result.stdout)
                
                if input("Apply these fixes? (y/n): ").lower() == 'y':
                    subprocess.run(["shfmt", "-w", file_path])
                    print("✅ Applied shfmt fixes")
        except FileNotFoundError:
            print("⚠️ shfmt not installed. Install with: apt install shfmt")

def install_dependencies():
    """Install required dependencies for syntax checking and fixing"""
    print("📦 Installing dependencies...")
    
    # Python dependencies
    subprocess.run([sys.executable, "-m", "pip", "install", "pyflakes", "autopep8"])
    
    # Check if running on Linux for shellcheck and shfmt
    if sys.platform.startswith('linux'):
        print("Installing Bash dependencies (requires sudo)...")
        subprocess.run(["sudo", "apt", "update"])
        subprocess.run(["sudo", "apt", "install", "-y", "shellcheck", "shfmt"])
    else:
        print("⚠️ shellcheck and shfmt are only available on Linux through apt.")
        print("   On macOS, you can install them with Homebrew:")
        print("   brew install shellcheck shfmt")
    
    print("✅ Dependencies installed")

def main():
    parser = argparse.ArgumentParser(description="Syntax checker and fixer for Python and Bash scripts")
    parser.add_argument("path", nargs="?", default=".", help="File or directory to check")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix syntax issues")
    parser.add_argument("--install", action="store_true", help="Install required dependencies")
    args = parser.parse_args()
    
    if args.install:
        install_dependencies()
        return
    
    path = args.path
    
    if os.path.isdir(path):
        success = scan_directory(path, args.fix)
    else:
        if path.endswith('.py'):
            if args.fix:
                fix_python_syntax(path)
                check_ps3_controller_mappings(path)
            success = check_python_syntax(path)
            
            if success and args.fix:
                get_recommended_fixes(path)
                
        elif path.endswith('.sh') or os.access(path, os.X_OK):
            if args.fix:
                fix_bash_syntax(path)
            success = check_bash_syntax(path)
            
            if success and args.fix:
                get_recommended_fixes(path)
        else:
            print(f"Unsupported file type: {path}")
            success = False
    
    if success:
        print("\n✅ Syntax check passed successfully")
    else:
        print("\n❌ Syntax check failed")
        sys.exit(1)

if __name__ == "__main__":
    main()

