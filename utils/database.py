from typing import List, Tuple, Optional, Dict, Any
import uuid
import streamlit as st
from supabase import Client # Importamos para tipado
from datetime import datetime, timedelta

# 1. Importar la conexión Supabase (Asumiendo que get_supabase_client está en utils/db)
try:
    from utils.db import get_supabase_client
except ImportError:
    st.error("Error: Falta el archivo 'utils/db.py' con la función get_supabase_client.")
    st.stop()


# ==================== UTILIDADES ====================

def _get_entidad_por_id(tabla: str, entity_id: int) -> Optional[Dict[str, Any]]:
    """Función genérica para obtener una entidad por su ID."""
    supabase = get_supabase_client()
    try:
        response = supabase.table(tabla).select("*").eq("id", entity_id).limit(1).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Error al obtener entidad {tabla} ID {entity_id}: {e}")
        return None

# ==================== FUNCIONES DE CLIENTES ====================

def get_clientes() -> List[Tuple[int, str]]:
    """Obtiene todos los clientes (id, nombre) - para selectores."""
    supabase = get_supabase_client()
    try:
        # Se obtiene el campo 'id' como integer y 'nombre' como string
        response = supabase.table("clientes").select("id, nombre").order("nombre").execute()
        # Mapear la lista de diccionarios a la lista de tuplas esperada
        return [(d['id'], d['nombre']) for d in response.data]
    except Exception as e:
        print(f"Error al obtener clientes: {e}")
        return []

def get_clientes_detallados(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Obtiene todos los clientes con detalles, filtrados opcionalmente por user_id."""
    supabase = get_supabase_client()
    try:
        query = supabase.table("clientes").select("*, users!inner(email)").order("nombre")
        if user_id:
            # Filtramos por el campo 'creado_por', que debe ser el UUID de Supabase Auth
            query = query.eq("creado_por", user_id)
            
        response = query.execute()
        
        # Mapeamos los datos para la presentación
        data = []
        for d in response.data:
            # Aseguramos que la fecha existe y es un objeto datetime
            fecha_creacion = d.get('fecha_creacion')
            if fecha_creacion and isinstance(fecha_creacion, str):
                try:
                    fecha_creacion = datetime.fromisoformat(fecha_creacion.replace('Z', '+00:00'))
                except ValueError:
                    fecha_creacion = None
                    
            data.append({
                'id': d['id'],
                'nombre': d['nombre'],
                'fecha_creacion': fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if fecha_creacion else 'N/A',
                # Los datos de la tabla 'users' vienen anidados.
                'creado_por': d.get('users', {}).get('email', 'Desconocido'), 
                'user_id': d.get('creado_por', 'N/A')
            })
        return data
    except Exception as e:
        print(f"Error al obtener clientes detallados: {e}")
        return []

def create_cliente(nombre: str, user_id: str) -> Optional[int]:
    """Crea un nuevo cliente. user_id es string (UUID)."""
    supabase = get_supabase_client()
    try:
        response = supabase.table("clientes").insert({
            "nombre": nombre,
            "creado_por": user_id # Usamos el UUID del usuario de Supabase Auth
        }).execute()
        # Supabase devuelve los datos del registro insertado, necesitamos el ID.
        return response.data[0]['id'] if response.data else None
    except Exception as e:
        print(f"Error al crear cliente: {e}")
        return None

def update_cliente(cliente_id: int, nombre: str, user_id: str) -> bool:
    """Actualiza un cliente existente."""
    supabase = get_supabase_client()
    try:
        # Añadimos .eq('creado_por', user_id) para seguridad a nivel de aplicación (RLS se encarga de esto en Supabase)
        response = supabase.table("clientes").update({
            "nombre": nombre
        }).eq("id", cliente_id).eq("creado_por", user_id).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error al actualizar cliente: {e}")
        return False

def delete_cliente(cliente_id: int, user_id: str) -> bool:
    """Elimina un cliente."""
    supabase = get_supabase_client()
    try:
        response = supabase.table("clientes").delete().eq("id", cliente_id).eq("creado_por", user_id).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error al eliminar cliente: {e}")
        return False


# ==================== FUNCIONES DE LUGARES DE TRABAJO ====================

def get_lugares_trabajo() -> List[Tuple[int, str]]:
    """Obtiene todos los lugares de trabajo (id, nombre)."""
    supabase = get_supabase_client()
    try:
        response = supabase.table("lugares_trabajo").select("id, nombre").order("nombre").execute()
        return [(d['id'], d['nombre']) for d in response.data]
    except Exception as e:
        print(f"Error al obtener lugares de trabajo: {e}")
        return []

def create_lugar_trabajo(nombre: str, user_id: str) -> Optional[int]:
    """Crea un nuevo lugar de trabajo. user_id es string (UUID)."""
    supabase = get_supabase_client()
    try:
        response = supabase.table("lugares_trabajo").insert({
            "nombre": nombre,
            "creado_por": user_id
        }).execute()
        return response.data[0]['id'] if response.data else None
    except Exception as e:
        print(f"Error al crear lugar de trabajo: {e}")
        return None


# ==================== FUNCIONES DE PRESUPUESTOS ====================

def save_presupuesto_completo(user_id: str, cliente_id: int, lugar_id: int, descripcion: str, items_data: Dict[str, Any], total_general: float) -> Optional[int]:
    """
    Guarda el presupuesto principal y sus ítems.
    Regresa el ID del presupuesto creado.
    """
    supabase = get_supabase_client()
    try:
        # 1. Guardar el presupuesto principal
        # El campo 'total' debe ser float
        presupuesto_data = {
            "creado_por": user_id, 
            "cliente_id": cliente_id,
            "lugar_trabajo_id": lugar_id,
            "descripcion": descripcion,
            "total": float(total_general),
            "num_items": sum(len(data['items']) for cat, data in items_data.items() if cat != 'general') + (1 if items_data['general'].get('mano_obra', 0) > 0 else 0)
        }
        
        response = supabase.table("presupuestos").insert(presupuesto_data).execute()
        nuevo_presupuesto_id = response.data[0]['id']
        
        # 2. Preparar los ítems para la inserción masiva
        items_to_insert = []
        for categoria, data in items_data.items():
            # Añadir Mano de Obra General si existe
            mano_obra_general = data.get('mano_obra', 0)
            if categoria == 'general' and mano_obra_general > 0:
                 items_to_insert.append({
                    "presupuesto_id": nuevo_presupuesto_id,
                    "nombre": "Mano de Obra General",
                    "categoria": "General", # Se asume una categoría 'General' para la MO general
                    "unidad": "Global",
                    "cantidad": 1.0,
                    "precio_unitario": float(mano_obra_general),
                    "total": float(mano_obra_general),
                    "notas": "Costo de mano de obra para el trabajo completo."
                })
            
            # Añadir ítems de categorías específicas
            for item in data['items']:
                # Asegurar que los valores numéricos son float
                items_to_insert.append({
                    "presupuesto_id": nuevo_presupuesto_id,
                    "nombre": item.get('nombre', 'Item sin nombre'),
                    "categoria": item.get('categoria', categoria),
                    "unidad": item.get('unidad', 'Unidad'),
                    "cantidad": float(item.get('cantidad', 0)),
                    "precio_unitario": float(item.get('precio_unitario', 0)),
                    "total": float(item.get('total', 0)),
                    "notas": item.get('notas', '')
                })

        # 3. Insertar todos los ítems
        if items_to_insert:
            supabase.table("items_en_presupuesto").insert(items_to_insert).execute()
        
        return nuevo_presupuesto_id
            
    except Exception as e:
        print(f"Error al guardar presupuesto completo: {e}")
        return None

def update_presupuesto_detalles(presupuesto_id: int, cliente_id: int, lugar_id: int, descripcion: str, total_general: float) -> bool:
    """Actualiza los campos principales del presupuesto."""
    supabase = get_supabase_client()
    try:
        response = supabase.table("presupuestos").update({
            "cliente_id": cliente_id,
            "lugar_trabajo_id": lugar_id,
            "descripcion": descripcion,
            "total": float(total_general)
        }).eq("id", presupuesto_id).execute() # <--- Se asegura que se actualice el presupuesto principal
        return len(response.data) > 0
    except Exception as e:
        print(f"Error al actualizar detalles del presupuesto {presupuesto_id}: {e}")
        return False
        
def delete_items_presupuesto(presupuesto_id: int) -> bool:
    """Elimina todos los ítems asociados a un presupuesto."""
    supabase = get_supabase_client()
    try:
        supabase.table("items_en_presupuesto").delete().eq("presupuesto_id", presupuesto_id).execute()
        return True
    except Exception as e:
        print(f"Error al eliminar ítems del presupuesto {presupuesto_id}: {e}")
        return False

def save_edited_presupuesto(presupuesto_id: int, user_id: str, cliente_id: int, lugar_id: int, descripcion: str, items_data: Dict[str, Any], total_general: float) -> Optional[int]:
    """
    Guarda los cambios de un presupuesto existente.
    1. Actualiza el presupuesto principal.
    2. Elimina todos los ítems anteriores.
    3. Inserta todos los ítems nuevos.
    """
    supabase = get_supabase_client()
    try:
        # 1. Actualizar el registro principal
        # El campo 'total' debe ser float
        num_items = sum(len(data['items']) for cat, data in items_data.items() if cat != 'general') + (1 if items_data['general'].get('mano_obra', 0) > 0 else 0)
        
        actualizacion_principal = supabase.table("presupuestos").update({
            "cliente_id": cliente_id,
            "lugar_trabajo_id": lugar_id,
            "descripcion": descripcion,
            "total": float(total_general),
            "num_items": num_items
        }).eq("id", presupuesto_id).eq("creado_por", user_id).execute()
        
        if not actualizacion_principal.data:
            print(f"Error: No se encontró el presupuesto {presupuesto_id} para actualizar o no tiene permiso.")
            return None
            
        # 2. Eliminar ítems anteriores
        delete_items_presupuesto(presupuesto_id)
        
        # 3. Preparar los ítems para la inserción masiva (similar a save_presupuesto_completo)
        items_to_insert = []
        for categoria, data in items_data.items():
            # Añadir Mano de Obra General si existe
            mano_obra_general = data.get('mano_obra', 0)
            if categoria == 'general' and mano_obra_general > 0:
                 items_to_insert.append({
                    "presupuesto_id": presupuesto_id,
                    "nombre": "Mano de Obra General",
                    "categoria": "General", 
                    "unidad": "Global",
                    "cantidad": 1.0,
                    "precio_unitario": float(mano_obra_general),
                    "total": float(mano_obra_general),
                    "notas": "Costo de mano de obra para el trabajo completo."
                })
            
            # Añadir ítems de categorías específicas
            for item in data['items']:
                # Asegurar que los valores numéricos son float
                items_to_insert.append({
                    "presupuesto_id": presupuesto_id,
                    "nombre": item.get('nombre', 'Item sin nombre'),
                    "categoria": item.get('categoria', categoria),
                    "unidad": item.get('unidad', 'Unidad'),
                    "cantidad": float(item.get('cantidad', 0)),
                    "precio_unitario": float(item.get('precio_unitario', 0)),
                    "total": float(item.get('total', 0)),
                    "notas": item.get('notas', '')
                })
            
        if items_to_insert:
            supabase.table("items_en_presupuesto").insert(items_to_insert).execute()
        
        return presupuesto_id
            
    except Exception as e:
        print(f"Error al guardar presupuesto editado: {e}")
        return None

def get_presupuesto_detallado(presupuesto_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene todos los detalles de un presupuesto por su ID."""
    supabase = get_supabase_client()
    try:
        # Obtener el registro principal del presupuesto
        presupuesto_response = supabase.table("presupuestos").select(
            "*, cliente:cliente_id(*), lugar:lugar_trabajo_id(*)"
        ).eq("id", presupuesto_id).limit(1).execute()
        
        if not presupuesto_response.data:
            return None
            
        presupuesto = presupuesto_response.data[0]
        
        # Obtener los ítems asociados
        items_response = supabase.table("items_en_presupuesto").select("*").eq("presupuesto_id", presupuesto_id).order("id").execute()
        
        # Estructurar la respuesta
        detalle = {
            "id": presupuesto.get('id'),
            "fecha": presupuesto.get('fecha_creacion'),
            "cliente": presupuesto.get('cliente'), # Viene anidado
            "lugar": presupuesto.get('lugar'),     # Viene anidado
            "descripcion": presupuesto.get('descripcion'),
            "total": presupuesto.get('total'),
            "items": items_response.data or []
        }
        return detalle

    except Exception as e:
        print(f"Error al obtener detalle del presupuesto {presupuesto_id}: {e}")
        return None

def get_presupuestos_usuario(user_id: str, filtros: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Obtiene los presupuestos de un usuario con filtros."""
    supabase = get_supabase_client()
    try:
        # Consulta con JOIN para obtener cliente y lugar
        query = supabase.table("presupuestos").select(
            "id, fecha_creacion, total, num_items, cliente:cliente_id(*), lugar:lugar_trabajo_id(*)"
        ).eq("creado_por", user_id) # Filtrado MANDATORIO por el ID de usuario (UUID)

        # Aplicar filtros
        if 'cliente_id' in filtros and filtros['cliente_id'] is not None:
            query = query.eq("cliente_id", filtros['cliente_id'])
        if 'lugar_id' in filtros and filtros['lugar_id'] is not None:
            query = query.eq("lugar_trabajo_id", filtros['lugar_id'])
        if 'fecha_inicio' in filtros and filtros['fecha_inicio'] is not None:
            # Filtro por fecha usando el formato ISO 8601 que espera Supabase
            query = query.gte("fecha_creacion", filtros['fecha_inicio'].isoformat())

        # Ordenar por fecha descendente
        response = query.order("fecha_creacion", desc=True).execute()

        # Mapear la respuesta para el formato esperado por Streamlit
        presupuestos_formateados = []
        for p in response.data:
            # Conversión segura de fecha
            fecha_creacion = p.get('fecha_creacion')
            if fecha_creacion and isinstance(fecha_creacion, str):
                try:
                    # Supabase devuelve ISO 8601 (con o sin Z)
                    fecha_obj = datetime.fromisoformat(fecha_creacion.replace('Z', '+00:00'))
                except ValueError:
                    fecha_obj = datetime(1970, 1, 1) # Fallback
            else:
                fecha_obj = datetime(1970, 1, 1)
                
            presupuestos_formateados.append({
                'id': p['id'],
                'fecha': fecha_obj,
                'total': float(p.get('total', 0)), # Asegurar que es float
                'num_items': p.get('num_items', 0),
                'cliente': p.get('cliente', {'nombre': 'N/A'}),
                'lugar': p.get('lugar', {'nombre': 'N/A'})
            })
            
        return presupuestos_formateados

    except Exception as e:
        print(f"Error al obtener presupuestos del usuario {user_id}: {e}")
        return []

def delete_presupuesto(presupuesto_id: int, user_id: str) -> bool:
    """
    Elimina un presupuesto y sus ítems asociados.
    Eliminación en cascada: primero ítems, luego el principal.
    """
    supabase = get_supabase_client()
    try:
        # 1. Eliminar ítems asociados (si RLS no está configurado para hacerlo en cascada)
        delete_items_presupuesto(presupuesto_id)

        # 2. Eliminar el presupuesto principal (asegurando pertenencia)
        response = supabase.table("presupuestos").delete().eq("id", presupuesto_id).eq("creado_por", user_id).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error al eliminar presupuesto completo {presupuesto_id}: {e}")
        return False

# ==================== FUNCIONES PARA ITEMS y CATEGORIAS ====================

def get_categorias() -> List[Tuple[int, str]]:
    """Obtiene todas las categorías existentes (id, nombre)"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("categorias").select("id, nombre").order("nombre").execute()
        return [(d['id'], d['nombre']) for d in response.data]
    except Exception as e:
        print(f"Error al obtener categorias: {e}")
        return []

def create_categoria(nombre: str, user_id: str) -> Optional[int]:
    """Crea una nueva categoría. user_id es string (UUID)."""
    supabase = get_supabase_client()
    try:
        response = supabase.table("categorias").insert({
            "nombre": nombre,
            "creado_por": user_id
        }).execute() 
        
        return response.data[0]['id'] if response.data else None
    except Exception as e:
        print(f"Error al crear categoria: {e}")
        return None