import subprocess

def get_systeminfo_output():
    try:
        output = subprocess.check_output("systeminfo", shell=True, encoding="utf-8")
        return output
    except Exception as e:
        print(">>> Error running systeminfo:", e)
        return ""

def get_cpu_output():
    try:
        output = subprocess.check_output("wmic cpu get name", shell=True, encoding="utf-8")
        return output
    except Exception as e:
        print(">>> Error running wmic cpu get name:", e)
        return ""

def get_ipconfig_output():
    try:
        output = subprocess.check_output("ipconfig", shell=True, encoding="utf-8")
        return output
    except Exception as e:
        print(">>> Error running ipconfig:", e)
        return ""

if __name__ == "__main__":
    print(">>> Please wait... Gathering system information.")
    print("============================")
    print("  OPERATING SYSTEM")
    sysinfo = get_systeminfo_output()
    for line in sysinfo.splitlines():
        if line.startswith("OS Name") or line.startswith("OS Version") or line.startswith("System Manufacturer") or line.startswith("System Model"):
            print(line)
    print("============================")
    print("  BIOS")
    for line in sysinfo.splitlines():
        if "System Type" in line:
            print(line)
    print("============================")
    print("  MEMORY")
    for line in sysinfo.splitlines():
        if line.startswith("Total Physical Memory") or line.startswith("Available Physical Memory") or line.startswith("Virtual Memory: Max Size") or line.startswith("Virtual Memory: Available") or line.startswith("Virtual Memory: In Use"):
            print(line)
    print("============================")
    print("  CPU")
    cpu_output = get_cpu_output()
    for line in cpu_output.splitlines():
        if "Name" not in line and line.strip():
            print(line)
    print("============================")
    print("  NETWORK ADDRESS")
    ipconfig = get_ipconfig_output()
    for line in ipconfig.splitlines():
        if "IPv4" in line or "IPv6" in line:
            print(line)
    print("============================") 