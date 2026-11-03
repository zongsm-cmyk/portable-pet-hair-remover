"""
Forwarder script to run scripts/build_store.py from root
"""
import sys
from pathlib import Path
import runpy

script_path = Path(__file__).resolve().parent / 'scripts' / 'build_store.py'
runpy.run_path(str(script_path), run_name='__main__')
