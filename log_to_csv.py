import re
import csv
from datetime import datetime

# Leer el archivo de log
with open('log_20260317.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Extraer datos
data = []
current_local = None
current_pos = None

# Patrón para "Local XXX:"
local_pattern = r'Local (\d+):'
# Patrón para "POS Y:"
pos_pattern = r'POS (\d+):'
# Patrón para los cierres (con o sin microsegundos)
cierre_pattern = r'Closed: (\d{4}-\d{2}-\d{2})\s+\d{2}:\d{2}:\d{2}(?:\.\d+)? \| ID: (\d+) \|'

for line in content.split('\n'):
    # Buscar Local
    local_match = re.search(local_pattern, line)
    if local_match:
        current_local = local_match.group(1)
        continue

    # Buscar POS
    pos_match = re.search(pos_pattern, line)
    if pos_match:
        current_pos = pos_match.group(1)
        continue

    # Buscar cierres
    cierre_match = re.search(cierre_pattern, line)
    if cierre_match and current_local and current_pos:
        closed_date = cierre_match.group(1)
        cierre_id = cierre_match.group(2)
        data.append({
            'localid': current_local,
            'pos': current_pos,
            'id': cierre_id,
            'closed': closed_date
        })

# Escribir CSV
with open('cierres_faltantes.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['localid', 'pos', 'id', 'closed'], delimiter='|')
    writer.writeheader()
    writer.writerows(data)

print(f"CSV creado: cierres_faltantes.csv")
print(f"Total de registros: {len(data)}")
