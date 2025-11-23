# OCPP-CAN Bus Simülasyonu

Elektrikli araç şarj istasyonları için OCPP ve CAN-bus iletişim simülasyonu.

**Büşra Gül - 180541037**

## Kurulum
```bash
pip install ocpp==0.17.0 websockets==11.0 python-can==4.2.2
```

### Linux için CAN kurulumu
```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

## Çalıştırma

3 farklı terminal açın:

**Terminal 1:**
```bash
python csms_server.py
```

**Terminal 2:**
```bash
python can_listener.py
```

**Terminal 3:**
```bash
python charge_point.py
```

## Dosyalar

- `csms_server.py` - Merkez sunucu
- `charge_point.py` - Şarj istasyonu
- `can_bridge.py` - OCPP → CAN dönüştürücü
- `can_listener.py` - CAN mesaj dinleyici
- `mitm_attack.py` - MitM saldırı testi

## MitM Testi

**Terminal 1:** `python csms_server.py`

**Terminal 2:** `python mitm_attack.py`

**Terminal 3:** `python can_listener.py`

**Terminal 4:** `charge_point.py` dosyasında 186. satırı düzenle:
```python
'ws://localhost:8888/CP001'  # 9000 → 8888
```
Sonra çalıştır: `python charge_point.py`

## Loglar

Loglar `logs/` klasöründe otomatik oluşturulur.

## Lisans

MIT
```

---

## 📄 DOSYA 2: requirements.txt
```
ocpp==0.17.0
websockets==11.0
python-can==4.2.2
```

---

## 📄 DOSYA 3: .gitignore
```
__pycache__/
*.py[cod]
*.pyc
logs/*.txt
logs/*.log
.vscode/
.idea/
*.swp
.DS_Store
venv/
env/
