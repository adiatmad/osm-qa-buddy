import ctypes
import os
import platform

MIN_RAM_GB = 2
AUTO_MAX_RAM_GB = 10
MANUAL_MAX_RAM_GB = 16
RESERVED_HOST_RAM_GB = 4


def get_total_memory_bytes():
    """Return physical RAM in bytes using the host OS standard library only."""
    if platform.system() == "Windows":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.dwLength = ctypes.sizeof(MemoryStatus)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            raise RuntimeError("Could not determine installed physical RAM.")
        return status.ullTotalPhys

    if hasattr(os, "sysconf"):
        try:
            return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        except (ValueError, OSError):
            pass

    raise RuntimeError("Could not determine installed physical RAM on this operating system.")


def total_memory_gb():
    return get_total_memory_bytes() / (1024 ** 3)


def automatic_ram_gb(total_gb=None):
    """Choose a conservative, deterministic JVM heap size."""
    total_gb = total_memory_gb() if total_gb is None else float(total_gb)
    if total_gb <= 4:
        return 2
    if total_gb <= 8:
        return 4
    if total_gb <= 16:
        return 8
    return AUTO_MAX_RAM_GB


def maximum_manual_ram_gb(total_gb=None):
    """Maximum manual heap while retaining a host-memory safety reserve."""
    total_gb = total_memory_gb() if total_gb is None else float(total_gb)
    return max(MIN_RAM_GB, min(MANUAL_MAX_RAM_GB, int(total_gb - RESERVED_HOST_RAM_GB)))


def validate_ram_gb(ram_gb, total_gb=None):
    """Validate a user-selected heap size before Docker/JOSM starts."""
    try:
        ram_gb = int(ram_gb)
    except (TypeError, ValueError):
        return False, "RAM must be a whole number of GB."

    if ram_gb < MIN_RAM_GB:
        return False, f"RAM must be at least {MIN_RAM_GB} GB."

    total_gb = total_memory_gb() if total_gb is None else float(total_gb)
    max_ram = maximum_manual_ram_gb(total_gb)
    if ram_gb > max_ram:
        return False, (
            f"{ram_gb} GB is too high for this machine. "
            f"With about {total_gb:.1f} GB physical RAM, the safe manual maximum is {max_ram} GB."
        )

    return True, ""
