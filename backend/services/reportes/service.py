from datetime import datetime, time
from models.database import AsignacionHistorial

def obtener_reporte(fecha_inicio: str = None, fecha_fin: str = None) -> list:
    if not fecha_inicio or not fecha_fin:
        return []

    try:
        # 1. Convertir y validar
        start_date = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        end_date = datetime.strptime(fecha_fin, '%Y-%m-%d').date()

        if start_date > end_date:
            raise Exception("La fecha de inicio no puede ser posterior a la fecha de fin.")

        # 2. Ajustar el rango para incluir TODO el día final
        # Combinamos la fecha de fin con las 23:59:59
        start_dt = datetime.combine(start_date, time.min) # 00:00:00
        end_dt = datetime.combine(end_date, time.max)   # 23:59:59

        # 3. Consulta con objetos datetime completos
        registros = AsignacionHistorial.query.filter(
            AsignacionHistorial.fecha_asignacion.between(start_dt, end_dt)
        ).all()

        resultado = []

        total_ventas = 0
        total_costos = 0
        
        
        for h in registros:
            venta = float(h.venta or 0)
            costo = float(h.costo_total or 0)
            
            total_ventas += venta
            total_costos += costo
        
        margen_total_general = round(((total_ventas - total_costos) / total_ventas * 100), 2) if total_ventas > 0 else 0
        
        
        for h in registros:
            venta = float(h.venta or 0)
            costo = float(h.costo_total or 0)
            
            margen_calculado = float(h.margin) if h.margin is not None else \
                            (round(((venta - costo) / venta * 100), 2) if venta > 0 else 0)
            
            resultado.append({
                "cod_flete": h.cod_flete,
                "cliente": h.flete.cliente if h.flete else "N/A",
                "placa": h.placa or "",
                "conductor": h.conductor or "",
                "fecha_asignacion": h.fecha_asignacion.strftime('%Y-%m-%d %H:%M'),
                "costo_total": costo,
                "venta": venta,
                "margen": margen_calculado,
                "margen_total_general": margen_total_general 
            })
            resultados = resultado
            print(f"datos enviados al frontes {resultados}")
        return resultado
        

    except ValueError:
        raise Exception("Formato de fecha inválido. Debe ser YYYY-MM-DD")