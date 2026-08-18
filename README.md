# Escáner de cercanía Bluetooth

Este proyecto usa [Bleak](https://bleak.readthedocs.io/en/latest/index.html) como dependencia.

Primero crea un entorno virtual de Python:

### Linux/MacOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### PowerShell:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

E instálalo:

```
pip install -r requirements.txt
```

**⚠️ En sistemas Linux puede que necesites instalar Tk como paquete del sistema:**

- Arch: `sudo pacman -S tk`
- Debian *(al menos en Linux Mint 22.3)*: `sudo apt install python3-tk`