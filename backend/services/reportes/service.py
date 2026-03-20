from datetime import datetime, time
from models.database import AsignacionHistorial

def obtener_reporte(fecha_inicio: str = None, fecha_fin: str = None) -> dict:
    print(f"\n>>> [LOG] Iniciando reporte: {fecha_inicio} al {fecha_fin}")
    
    if not fecha_inicio or not fecha_fin:
        return {"error": "Fechas faltantes"}

    try:
        # 1. Preparación de fechas
        start_date = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        end_date = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date, time.max)

        # 2. Consulta a la base de datos
        registros = AsignacionHistorial.query.filter(
            AsignacionHistorial.fecha_asignacion.between(start_dt, end_dt)
        ).all()
        
        print(f">>> [LOG] Registros encontrados: {len(registros)}")

        # 3. Primer paso: Calcular totales para el margen general
        total_ventas = sum(float(h.venta or 0) for h in registros)
        total_costos = sum(float(h.costo_total or 0) for h in registros)
        margen_total_general = round(((total_ventas - total_costos) / total_ventas * 100), 2) if total_ventas > 0 else 0

        # 4. Segundo paso: Armar el detalle (la lista)
        resultado_detalle = []
        for h in registros:
            venta = float(h.venta or 0)
            costo = float(h.costo_total or 0)
            
            # Calculamos el margen por fila
            margen_fila = float(h.margin) if h.margin is not None else \
                         (round(((venta - costo) / venta * 100), 2) if venta > 0 else 0)
            
            resultado_detalle.append({
                "cod_flete": h.cod_flete,
                "cliente": h.flete.cliente if h.flete else "N/A",
                "placa": h.placa or "",
                "conductor": h.conductor or "",
                "fecha_asignacion": h.fecha_asignacion.strftime('%Y-%m-%d %H:%M'),
                "costo_total": costo,
                "venta": venta,
                "margen": margen_fila,
            })

        # 5. ESTRUCTURA FINAL DEL JSON
        respuesta_final = {
            "fletes": resultado_detalle,                # La lista de objetos
            "margen_total_general": margen_total_general, # El dato único
            "total_registros": len(resultado_detalle)   # Metadata útil
        }

        
        print(f"fletes individuales:{resultado_detalle} ")
        print(f"    - Margen General: {respuesta_final['margen_total_general']}%")
        print(f"    - Cantidad de fletes: {len(respuesta_final['fletes'])}")
        
        return respuesta_final

    except Exception as e:
        print(f">>> [LOG ERROR] Ocurrió un fallo: {str(e)}")
        raise e