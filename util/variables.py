dist_afectacion = ['1.6', '5', '7.3', '9.5', '12.5', '14.5', '20.9', '37.5']

dist_explosion = ['0.4', '2', '4.3', '6.4', '14']

descarga_instantanea = ['R1', 'C1', 'P1']

gases = ['Gas Natural', "GLP"]

#### AAD #####
header1_aad = (
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

header2_aad = (
    [''] * 9 + dist_afectacion * 3
    + ['Dia 100% LII', 'Dia 50% LII', 'Noche 100% LII', 'Noche 50% LII']
    + dist_explosion * 2
)

column_names_aad = [header1_aad, header2_aad]

#### AAI #####
header1_aai = (
    [
        'CUERPO DE AGUA',
        'TRAMO',
        'SUSTANCIA',
        'INICIADOR',
        'FRECUENCIA FALLA (año x m -1)',
        'MODIFICADORES FRECUENCIA',
    ]
    + ['RADIACIÓN TÉRMICA (kW/m2) INCENDIO DE PISCINA'] * 8
    + ['RADIACIÓN TÉRMICA (kW/m2) CHORRO DE FUEGO'] * 8
    + ['RADIACIÓN TÉRMICA (kW/m2) BOLA DE FUEGO'] * 8
    + ['DISPERSIÓN DE NUBE INFLAMABLE - DISTANCIAS DE AFECTACIÓN (m)'] * 4
    + ['SOBREPRESION (PSI) EXPLOSION DIA'] * 5
    + ['SOBREPRESION (PSI) EXPLOSION NOCHE'] * 5
)

header2_aai = (
    [''] * 6 + dist_afectacion * 3
    + ['Dia 100% LII', 'Dia 50% LII', 'Noche 100% LII', 'Noche 50% LII']
    + dist_explosion * 2
)

# Define columns name
column_names_aai = [header1_aai, header2_aai]

distancias = list(range(0, 1000)) + list(range(1000, 7500, 500))

####SOCIAL####
fatalidades = [1, 50, 100, 1000]
limite_inferior = [0.000477742562115388, 0.000002, 7.5789157091564E-07, 3.15478672240097E-08]
limite_superior = [0.0478040492097267, 0.0002, 0.0000757484899840227, 3.01597610661533E-06]
afectacion_baja = [1.6, 5, '0,4 psi', 'LII/2']
