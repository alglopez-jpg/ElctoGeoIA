"""Supuestos de redistribución de coaliciones -> partidos, por elección.

Regla general (documentada y discutible):
- Coalición de N partidos -> reparto equitativo (1/N) de los votos de la
  columna de coalición. Es el supuesto más neutral cuando no se tiene el
  convenio de coalición; el INE usa porcentajes del convenio para efectos
  de registro, que pueden sustituirse aquí cuando se conozcan.
- Partidos desaparecidos o sin continuidad -> columna "otros".

Cada entrada: {columna_del_csv: {partido: peso}}. Las columnas de partidos
suelos se mapean 1:1 (implícito).
"""

COALICIONES = {
    2012: {
        "pri-pvem": {"pri": 0.5, "pvem": 0.5},
        "prd-pt-mc": {"prd": 1/3, "pt": 1/3, "mc": 1/3},
    },
    2015: {
        "pan.pna": {"pan": 0.5, "otros": 0.5},
        "pri.pvem": {"pri": 0.5, "pvem": 0.5},
        "prd.pt": {"prd": 0.5, "pt": 0.5},
    },
    2018: {
        "PAN_PRD_MC": {"pan": 1/3, "prd": 1/3, "mc": 1/3},
        "PAN_PRD": {"pan": 0.5, "prd": 0.5},
        "PAN_MC": {"pan": 0.5, "mc": 0.5},
        "PRD_MC": {"prd": 0.5, "mc": 0.5},
        "PRI_PVEM_NA": {"pri": 1/3, "pvem": 1/3, "otros": 1/3},
        "PRI_PVEM": {"pri": 0.5, "pvem": 0.5},
        "PRI_NA": {"pri": 0.5, "otros": 0.5},
        "PVEM_NA": {"pvem": 0.5, "otros": 0.5},
        "PT_MORENA_PES": {"pt": 1/3, "morena": 1/3, "otros": 1/3},
        "PT_MORENA": {"pt": 0.5, "morena": 0.5},
        "PT_PES": {"pt": 0.5, "otros": 0.5},
        "MORENA_PES": {"morena": 0.5, "otros": 0.5},
    },
    2021: {
        "PAN-PRI-PRD": {"pan": 1/3, "pri": 1/3, "prd": 1/3},
        "PAN-PRI": {"pan": 0.5, "pri": 0.5},
        "PAN-PRD": {"pan": 0.5, "prd": 0.5},
        "PRI-PRD": {"pri": 0.5, "prd": 0.5},
        "PVEM-PT-MORENA": {"pvem": 1/3, "pt": 1/3, "morena": 1/3},
        "PVEM-PT": {"pvem": 0.5, "pt": 0.5},
        "PVEM-MORENA": {"pvem": 0.5, "morena": 0.5},
        "PT-MORENA": {"pt": 0.5, "morena": 0.5},
    },
    2024: {
        "PAN_PRI_PRD": {"pan": 1/3, "pri": 1/3, "prd": 1/3},
        "PAN_PRI": {"pan": 0.5, "pri": 0.5},
        "PAN_PRD": {"pan": 0.5, "prd": 0.5},
        "PRI_PRD": {"pri": 0.5, "prd": 0.5},
        "PVEM_PT_MORENA": {"pvem": 1/3, "pt": 1/3, "morena": 1/3},
        "PVEM_PT": {"pvem": 0.5, "pt": 0.5},
        "PVEM_MORENA": {"pvem": 0.5, "morena": 0.5},
        "PT_MORENA": {"pt": 0.5, "morena": 0.5},
    },
}

# Mapeo de columnas de partidos sueltos -> partido canónico del panel.
PARTIDOS = {
    2012: {"pan": "pan", "pri": "pri", "prd": "prd", "pvem": "pvem",
           "pt": "pt", "mc": "mc", "pna": "otros"},
    2015: {"pan": "pan", "pri": "pri", "prd": "prd", "pvem": "pvem",
           "pt": "pt", "mc": "mc", "pna": "otros", "morena": "morena",
           "ph": "otros", "pes": "otros"},
    2018: {"PAN": "pan", "PRI": "pri", "PRD": "prd", "PVEM": "pvem",
           "PT": "pt", "MOVIMIENTO CIUDADANO": "mc",
           "NUEVA ALIANZA": "otros", "MORENA": "morena",
           "ENCUENTRO SOCIAL": "otros",
           "CAND_IND_01": "otros", "CAND_IND_02": "otros"},
    2021: {"PAN": "pan", "PRI": "pri", "PRD": "prd", "PVEM": "pvem",
           "PT": "pt", "MC": "mc", "MORENA": "morena", "PES": "otros",
           "RSP": "otros", "FXM": "otros", "CI": "otros"},
    2024: {"PAN": "pan", "PRI": "pri", "PRD": "prd", "PVEM": "pvem",
           "PT": "pt", "MC": "mc", "MORENA": "morena"},
}

PARTIDOS_PANEL = ["pan", "pri", "prd", "pvem", "pt", "mc", "morena", "otros"]
