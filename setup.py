import sys
from cx_Freeze import setup, Executable

build_exe_options = {"packages": ["urllib", "jsonpickle", "cefpython3", "rsa", "logging","threading", "json","socket", "socketserver"]}

setup(
    name = "Chrome",
    version = "3.1",
    description = "Chrome",
    options = {"build_exe": build_exe_options},
    executables = [Executable("run.py", base = "Win32GUI")])
