# run.pyw — pythonw runs this with NO console window on Windows
# Just rename the entry point to .pyw so Windows uses pythonw.exe automatically
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import main
main()
