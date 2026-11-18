import sys
try:
    import paramiko
    print("paramiko", paramiko.__version__)
except Exception as e:
    print("missing:", e)
print("python", sys.version.split()[0])
