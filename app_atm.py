import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import math

# --- 1. DATOS INICIALES ---
# NOTA: Los datos de ejemplo están en el futuro (2025). 
# Los mantendremos, pero la lógica de fechas se centrará en los días restantes.

DATOS_CAJEROS = [
    {
        'id': 'ATM-001',
        'codigoAgencia': 'AG-001',
        'nombreAgencia': 'Agencia Centro Lima',
        'ubicacion': 'Sucursal Centro',
        'tipo': 'reciclador',
        'saldoActual': 45000,
        'capacidadMaxima': 100000,
        'pronostico7dias': 38000,
        'consumoReal': 42000,
        'denominaciones': {'200': 50, '100': 100, '50': 150, '20': 200},
        'ultimoAbastecimiento': '2025-11-28',
        'estado': 'operativo',
        'montoAbastecer': 0
    },
    {
        'id': 'ATM-002',
        'codigoAgencia': 'AG-002',
        'nombreAgencia': 'Agencia Miraflores',
        'ubicacion': 'Mall Plaza',
        'tipo': 'retiro',
        'saldoActual': 15000,
        'capacidadMaxima': 80000,
        'pronostico7dias': 52000,
        'consumoReal': 48000,
        'denominaciones': {'200': 20, '100': 30, '50': 80, '20': 150},
        'ultimoAbastecimiento': '2025-11-25',
        'estado': 'alerta',
        'montoAbastecer': 0
    },
    {
        'id': 'ATM-003',
        'codigoAgencia': 'AG-001',
        'nombreAgencia': 'Agencia Centro Lima',
        'ubicacion': 'Aeropuerto',
        'tipo': 'reciclador',
        'saldoActual': 72000,
        'capacidadMaxima': 150000,
        'pronostico7dias': 65000,
        'consumoReal': 60000,
        'denominaciones': {'200': 120, '100': 180, '50': 200, '20': 250},
        'ultimoAbastecimiento': '2025-12-01',
        'estado': 'operativo',
        'montoAbastecer': 0
    },
    {
        'id': 'ATM-004',
        'codigoAgencia': 'AG-003',
        'nombreAgencia': 'Agencia San Isidro',
        'ubicacion': 'Universidad',
        'tipo': 'retiro',
        'saldoActual': 8000,
        'capacidadMaxima': 60000,
        'pronostico7dias': 35000,
        'consumoReal': 32000,
        'denominaciones': {'200': 10, '100': 20, '50': 40, '20': 100},
        'ultimoAbastecimiento': '2025-11-22',
        'estado': 'critico',
        'montoAbastecer': 0
    },
    {
        'id': 'ATM-005',
        'codigoAgencia': 'AG-002',
        'nombreAgencia': 'Agencia Miraflores',
        'ubicacion': 'Centro Comercial',
        'tipo': 'reciclador',
        'saldoActual': 12000,
        'capacidadMaxima': 90000,
        'pronostico7dias': 45000,
        'consumoReal': 43000,
        'denominaciones': {'200': 15, '100': 25, '50': 60, '20': 120},
        'ultimoAbastecimiento': '2025-11-24',
        'estado': 'critico',
        'montoAbastecer': 0
    },
    {
        'id': 'ATM-006',
        'codigoAgencia': 'AG-003',
        'nombreAgencia': 'Agencia San Isidro',
        'ubicacion': 'Torre Empresarial',
        'tipo': 'retiro',
        'saldoActual': 28000,
        'capacidadMaxima': 70000,
        'pronostico7dias': 30000,
        'consumoReal': 28000,
        'denominaciones': {'200': 40, '100': 60, '50': 80, '20': 100},
        'ultimoAbastecimiento': '2025-11-29',
        'estado': 'alerta',
        'montoAbastecer': 0
    }
]

# --- 2. FUNCIONES DE LÓGICA DE NEGOCIO ---

def formatear_moneda(valor):
    """Formatea un valor a soles peruanos sin decimales."""
    return f"S/ {valor:,.0f}".replace(",", "_").replace(".", ",").replace("_", ".")

def calcular_dias_de_efectivo(cajero):
    """Calcula los días restantes de efectivo basándose en el consumo semanal."""
    if cajero['consumoReal'] <= 0:
        return math.inf  # Si no hay consumo, efectivo infinito
    consumo_diario = cajero['consumoReal'] / 7
    dias_restantes = cajero['saldoActual'] / consumo_diario
    return max(0, dias_restantes)

def calcular_saldo_por_dia(cajero, dia):
    """Proyecta el saldo restante en el día T+dia."""
    if cajero['consumoReal'] <= 0:
        return cajero['saldoActual']
    consumo_diario = cajero['consumoReal'] / 7
    saldo_en_dia = cajero['saldoActual'] - (consumo_diario * dia)
    return max(0, saldo_en_dia)

def calcular_recomendacion(cajero):
    """Genera la recomendación de abastecimiento."""
    dias_restantes = calcular_dias_de_efectivo(cajero)
    
    # Condición de abastecimiento: menos de 3 días O saldo actual menor al pronóstico
    necesita_abastecimiento = dias_restantes < 3 or cajero['saldoActual'] < cajero['pronostico7dias']
    
    prioridad = 'Baja'
    if dias_restantes < 1:
        prioridad = 'Alta'
        cajero['estado'] = 'critico'
    elif dias_restantes < 3:
        prioridad = 'Media'
        cajero['estado'] = 'alerta'
    else:
        cajero['estado'] = 'operativo'

    monto_sugerido = cajero['capacidadMaxima'] - cajero['saldoActual'] if necesita_abastecimiento else 0
    
    return {
        'necesita': necesita_abastecimiento,
        'diasRestantes': f"{dias_restantes:.1f}",
        'montoSugerido': monto_sugerido,
        'prioridad': prioridad,
        'estado_actualizado': cajero['estado']
    }

def get_estado_color(estado):
    """Devuelve el color del estado en formato hexadecimal para Streamlit."""
    if estado == 'critico':
        return '#EF4444' # Rojo 500
    elif estado == 'alerta':
        return '#F59E0B' # Amarillo 500
    return '#10B981' # Verde 500

# --- 3. GESTIÓN DEL ESTADO EN STREAMLIT ---

# Inicializar el estado de la sesión si es la primera vez que se carga
if 'cajeros' not in st.session_state:
    st.session_state.cajeros = DATOS_CAJEROS
if 'filtro_estado' not in st.session_state:
    st.session_state.filtro_estado = 'todos'
if 'filtro_agencia' not in st.session_state:
    st.session_state.filtro_agencia = 'todas'
if 'filtro_periodo' not in st.session_state:
    st.session_state.filtro_periodo = 'todos'
if 'cajero_seleccionado' not in st.session_state:
    st.session_state.cajero_seleccionado = None

# --- 4. LAYOUT Y FILTROS EN LA BARRA LATERAL ---

st.set_page_config(layout="wide", page_title="Gestión de Cajeros ATM")

st.sidebar.title("🛠️ Filtros y Acciones")

# Filtro de Agencia
agencias_unicas = list(set([c['codigoAgencia'] for c in st.session_state.cajeros]))
agencias_display = {'todas': 'Todas las Agencias'}
for c in st.session_state.cajeros:
    agencias_display[c['codigoAgencia']] = f"{c['codigoAgencia']} - {c['nombreAgencia']}"
    
filtro_agencia = st.sidebar.selectbox(
    "Filtrar por Agencia:",
    options=list(agencias_display.keys()),
    format_func=lambda x: agencias_display[x],
    key='filtro_agencia'
)

# Filtro de Periodo
periodo_options = {
    'todos': 'Todos los periodos',
    't-0': 'T-0 (Hoy) - Con efectivo hoy',
    't-1': 'T-1 (Mañana) - Con efectivo hasta mañana',
    't-2': 'T-2 - Con efectivo hasta dentro de 2 días',
    't-3': 'T-3 - Con efectivo hasta dentro de 3 días',
    't-7': 'T-7 - Con efectivo hasta dentro de 7 días',
}

filtro_periodo = st.sidebar.selectbox(
    "Filtrar por Periodo de Efectivo:",
    options=list(periodo_options.keys()),
    format_func=lambda x: periodo_options[x],
    key='filtro_periodo'
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filtro por Estado")

# Filtro de Estado (Botones con lógica de conteo)
col_estados = st.sidebar.columns(3)

def set_filtro_estado(estado):
    st.session_state.filtro_estado = estado

# Contar cuántos cajeros cumplen con el filtro de agencia Y el filtro de estado
def contar_filtrados(estado):
    return len([
        c for c in st.session_state.cajeros 
        if c['estado'] == estado and 
           (st.session_state.filtro_agencia == 'todas' or c['codigoAgencia'] == st.session_state.filtro_agencia)
    ])

# Botones de estado
with col_estados[0]:
    if st.button(f"🔴 Crítico ({contar_filtrados('critico')})", use_container_width=True):
        set_filtro_estado('critico')
with col_estados[1]:
    if st.button(f"🟡 Alerta ({contar_filtrados('alerta')})", use_container_width=True):
        set_filtro_estado('alerta')
with col_estados[2]:
    if st.button(f"🟢 Operativo ({contar_filtrados('operativo')})", use_container_width=True):
        set_filtro_estado('operativo')

if st.sidebar.button(f"🌐 Mostrar Todos ({len(st.session_state.cajeros)})", use_container_width=True):
    set_filtro_estado('todos')
    
# --- 5. APLICACIÓN DE FILTROS ---

cajeros_filtrados = []

for c in st.session_state.cajeros:
    # 1. Filtro de Agencia
    cumple_agencia = st.session_state.filtro_agencia == 'todas' or c['codigoAgencia'] == st.session_state.filtro_agencia
    
    # 2. Filtro de Estado
    cumple_estado = st.session_state.filtro_estado == 'todos' or c['estado'] == st.session_state.filtro_estado
    
    # 3. Filtro de Período
    cumple_periodo = True
    if st.session_state.filtro_periodo != 'todos':
        dia = int(st.session_state.filtro_periodo.replace('t-', ''))
        saldo_en_dia = calcular_saldo_por_dia(c, dia)
        cumple_periodo = saldo_en_dia > 0
        
    if cumple_agencia and cumple_estado and cumple_periodo:
        # Calcular la recomendación para actualizar el estado y los días restantes
        c.update(calcular_recomendacion(c))
        cajeros_filtrados.append(c)

# -------------------------------------------------------------
# 6. ENCABEZADO Y PREDICCIÓN DE ABASTECIMIENTO
# -------------------------------------------------------------

st.title("Sistema de Gestión de Cajeros Automáticos")
st.markdown("Monitoreo y decisión de abastecimiento en tiempo real.")
st.markdown("---")

# Resumen de abastecimiento
cajeros_para_abastecer = [
    c for c in st.session_state.cajeros 
    if (c['estado'] == 'critico' or c['estado'] == 'alerta') and c['montoAbastecer'] > 0
]
total_abastecer = sum(c['montoAbastecer'] for c in cajeros_para_abastecer)

if total_abastecer > 0:
    st.info(f"""
        **🛒 Total a Abastecer Programado:** **{formatear_moneda(total_abastecer)}** en **{len(cajeros_para_abastecer)}** cajeros.
        (Presiona 'Enviar Correos' para notificar a las agencias.)
    """)
    if st.button("📧 Enviar Correos a Agencias"):
        st.success(f"Notificaciones de abastecimiento enviadas para {len(cajeros_para_abastecer)} cajeros.")
        # Lógica de limpiar montos o registrar el abastecimiento aquí si fuera un sistema real
        # st.session_state.cajeros = [
        #     {**c, 'montoAbastecer': 0} if c['montoAbastecer'] > 0 else c
        #     for c in st.session_state.cajeros
        # ]


# -------------------------------------------------------------
# 7. VISUALIZACIÓN DE CAJEROS (GRID)
# -------------------------------------------------------------

# Usar columnas de Streamlit para simular el grid de tarjetas (2 columnas)
col1, col2 = st.columns(2)
cols = [col1, col2]
col_idx = 0

if not cajeros_filtrados:
    st.warning("No se encontraron cajeros que coincidan con los filtros seleccionados.")

for cajero in cajeros_filtrados:
    with cols[col_idx % 2]: # Alternar entre col1 y col2
        
        # --- Configuración de la Tarjeta ---
        estado_color = get_estado_color(cajero['estado'])
        porcentaje_saldo = (cajero['saldoActual'] / cajero['capacidadMaxima']) * 100
        
        # Usamos st.container para crear la tarjeta con un borde de color basado en el estado
        st.markdown(f"""
        <div style="border-left: 5px solid {estado_color}; 
                    padding: 15px; 
                    margin-bottom: 20px; 
                    border-radius: 8px; 
                    background-color: white; 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        """, unsafe_allow_html=True)
        
        # Encabezado (ID y Estado)
        st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h3 style="margin: 0; font-size: 1.5em; font-weight: bold;">{cajero['id']}</h3>
                    <p style="margin: 0; color: #6B7280; font-size: 0.9em;">📍 {cajero['ubicacion']}</p>
                    <p style="margin: 0; color: #4F46E5; font-size: 0.8em; font-weight: 500;">🏛️ {cajero['nombreAgencia']}</p>
                </div>
                <span style="background-color: {estado_color}1A; color: {estado_color}; padding: 4px 8px; border-radius: 999px; font-weight: bold; font-size: 0.8em;">
                    {cajero['estado'].upper()}
                </span>
            </div>
            <hr style="margin-top: 10px; margin-bottom: 10px; border-top: 1px solid #E5E7EB;">
        """, unsafe_allow_html=True)

        # Proyección de Efectivo
        st.markdown(f"**Proyección de Efectivo:** **{cajero['diasRestantes']} días**")
        
        # Barra de Proyección T-0 a T-7
        st.markdown('<div style="display: flex; gap: 4px; margin-top: 8px; margin-bottom: 15px;">', unsafe_allow_html=True)
        for dia in range(8):
            saldo_dia = calcular_saldo_por_dia(cajero, dia)
            tiene_efectivo = saldo_dia > 0
            color = '#10B981' if tiene_efectivo else '#EF4444' # Verde o Rojo
            st.markdown(f"""
                <div style="flex: 1; height: 18px; background-color: {color}; border-radius: 4px; 
                            display: flex; align-items: center; justify-content: center; 
                            color: white; font-size: 0.7em;" 
                            title="T+{dia}: {formatear_moneda(saldo_dia)}">
                    T{dia}
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Barra de Saldo Actual
        st.markdown(f"""
            <p style="font-size: 0.9em; margin-bottom: 4px;">
                Saldo Actual: <span style="font-weight: bold; color: #4F46E5;">{formatear_moneda(cajero['saldoActual'])}</span> 
                ({porcentaje_saldo:.0f}% de {formatear_moneda(cajero['capacidadMaxima'])})
            </p>
        """, unsafe_allow_html=True)
        st.progress(porcentaje_saldo / 100)

        # Métricas (Pronóstico y Consumo)
        col_metricas = st.columns(2)
        col_metricas[0].metric("Pronóstico 7d", formatear_moneda(cajero['pronostico7dias']))
        col_metricas[1].metric("Consumo Real 7d", formatear_moneda(cajero['consumoReal']))
        
        # Input y Botón de Detalle
        if cajero['necesita']:
            monto_sugerido = cajero['montoSugerido']
            
            def update_monto_abastecer(atm_id):
                # Función para manejar el cambio en el input
                monto = st.session_state[f'monto_{atm_id}']
                # Encuentra y actualiza el cajero en el estado de la sesión
                for i, c in enumerate(st.session_state.cajeros):
                    if c['id'] == atm_id:
                        st.session_state.cajeros[i]['montoAbastecer'] = float(monto) if monto else 0
                        break
            
            st.markdown("---")
            st.warning(f"⚠️ **PRIORIDAD: {cajero['prioridad'].upper()}** Sugerido: {formatear_moneda(monto_sugerido)}")
            
            # Input para Monto a Abastecer
            st.number_input(
                f"Monto a Abastecer {cajero['id']} (S/):",
                min_value=0,
                max_value=cajero['capacidadMaxima'],
                value=cajero.get('montoAbastecer', 0),
                step=100,
                key=f'monto_{cajero["id"]}',
                on_change=update_monto_abastecer,
                args=(cajero['id'],)
            )

        if st.button(f"Ver Detalle {cajero['id']}", key=f'detalle_{cajero["id"]}', use_container_width=True):
            st.session_state.cajero_seleccionado = cajero
            st.rerun() # Forzar rerun para mostrar el modal

        st.markdown("</div>", unsafe_allow_html=True)

    col_idx += 1

# -------------------------------------------------------------
# 8. MODAL DE DETALLE (se muestra solo si hay un cajero seleccionado)
# -------------------------------------------------------------

if st.session_state.cajero_seleccionado:
    cajero_det = st.session_state.cajero_seleccionado
    
    # Usar un componente personalizado para simular el modal flotante
    st.markdown("""
        <style>
        .modal-background {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .modal-content {
            background-color: white;
            padding: 30px;
            border-radius: 12px;
            max-width: 600px;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }
        </style>
        <div class="modal-background">
            <div class="modal-content">
    """, unsafe_allow_html=True)
    
    st.header(f"Detalle: {cajero_det['id']}")
    st.caption(f"Ubicación: {cajero_det['ubicacion']} | Último Abastecimiento: {cajero_det['ultimoAbastecimiento']}")
    
    st.subheader("Información Clave")
    col_info = st.columns(3)
    col_info[0].metric("Saldo Actual", formatear_moneda(cajero_det['saldoActual']))
    col_info[1].metric("Capacidad Máxima", formatear_moneda(cajero_det['capacidadMaxima']))
    col_info[2].metric("Tipo", cajero_det['tipo'].capitalize())
    
    st.subheader("Denominaciones Disponibles")
    denominaciones_data = []
    for denom, cant in cajero_det['denominaciones'].items():
        denominaciones_data.append({
            'Denominación (S/)': int(denom),
            'Cantidad': cant,
            'Valor Total': formatear_moneda(int(denom) * cant)
        })
    st.dataframe(pd.DataFrame(denominaciones_data), hide_index=True, use_container_width=True)
    
    if st.button("Cerrar Detalle", key='cerrar_detalle_modal'):
        st.session_state.cajero_seleccionado = None
        st.rerun()
        
    st.markdown("</div></div>", unsafe_allow_html=True)
