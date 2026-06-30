import os

def is_path_safe(base, target):
    base = os.path.abspath(base)
    target = os.path.abspath(target)
    if base == '/':
        allowed_prefixes = [
            '/etc/enigma2/',
            '/usr/share/enigma2/',
            '/usr/lib/enigma2/python/Plugins/Extensions/RangoPolishChannelsUpdater/',
            '/media/hdd/',
            '/media/usb/',
            '/media/hdd2/',
            '/media/usb2/',
            '/picon/'
        ]
        for prefix in allowed_prefixes:
            if os.path.commonpath([prefix, target]) == prefix:
                return True
        return False
    return os.path.commonpath([base, target]) == base

print(f"Base: /, Target: /etc/enigma2/userbouquet.tv -> {is_path_safe('/', '/etc/enigma2/userbouquet.tv')}")
print(f"Prefix: /etc/enigma2/, Target: /etc/enigma2/userbouquet.tv -> {os.path.commonpath(['/etc/enigma2/', '/etc/enigma2/userbouquet.tv'])}")
