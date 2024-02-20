dist_afectacion = ['1.6', '5', '7.3', '9.5', '12.5', '14.5', '20.9', '37.5']

dist_explosion = ['0.4', '2', '4.3', '6.4', '14']

descarga_instantanea = ['R1', 'C1', 'P1']

gases = ['Gas Natural', "GLP"]

header1 = (
    [
        'CODIGO ESCENARIO',
        'EQUIPO',
        'INICIADOR',
        'SUSTANCIA',
        'FRECUENCIA FALLA (año x m -1)',
        'MODIFICADORES FRECUENCIA',
        'DIÁMETRO ROTURA (metros)',
        'VOLUMEN (bbls)',
        'TASA (kg/s)'
    ]
    + ['RADIACIÓN TÉRMICA (kW/m2) INCENDIO DE PISCINA'] * 8
    + ['RADIACIÓN TÉRMICA (kW/m2) CHORRO DE FUEGO'] * 8
    + ['RADIACIÓN TÉRMICA (kW/m2) BOLA DE FUEGO'] * 8
    + ['DISPERSIÓN DE NUBE INFLAMABLE - DISTANCIAS DE AFECTACIÓN (m)'] * 4
    + ['SOBREPRESION (PSI) EXPLOSION DIA'] * 5
    + ['SOBREPRESION (PSI) EXPLOSION NOCHE'] * 5
)

header2 = (
    [''] * 9 + dist_afectacion * 3
    + ['Dia 100% LII', 'Dia 50% LII', 'Noche 100% LII', 'Noche 50% LII']
    + dist_explosion * 2
)

# Define columns name
column_names = [header1, header2]

distancias = list(range(0, 1000)) + list(range(1000, 7500, 500))
