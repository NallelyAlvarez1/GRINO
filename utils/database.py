from typing import List, Tuple, Optional, Dict, Any
import uuid
import streamlit as st
from supabase import Client
from datetime import datetime, timedelta

# 1. Importar la conexión Supabase
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

def get_clientes(user_id: Optional[str] = None) -> List[Tuple[int, str]]:
    """Obtiene todos los clientes (id, nombre) - para selectores."""
    supabase = get_supabase_client()
    try:
        query = supabase.table("clientes").select("id, nombre").order("nombre")
        # Filtrar por usuario si se proporciona
        if user_id:
            query = query.eq("creado_por", user_id)
            
        response = query.execute()
        return [(d['id'], d['nombre']) for d in response.data]
    except Exception as e:
        print(f"Error al obtener clientes: {e}")
        return []

def get_clientes_detallados(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Obtiene todos los clientes con detalles, filtrados por user_id (UUID)."""
    supabase = get_supabase_client()
    try:
        query = supabase.table("clientes").select("*").order("nombre")
        if user_id:
            # Filtramos por el campo 'creado_por' que ahora es UUID
            query = query.eq("creado_por", user_id)
            
        response = query.execute()
        
        # Mapeamos los datos para la presentación
        data = []
        for d in response.data:
            fecha_creacion = d.get('fecha_registro')
            if fecha_creacion and isinstance(fecha_creacion, str):
                try:
                    fecha_creacion = datetime.fromisoformat(fecha_creacion.replace('Z', '+00:00'))
                except ValueError:
                    fecha_creacion = None
                    
            data.append({
                'id': d['id'],
                'nombre': d['nombre'],
                'fecha_creacion': fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if fecha_creacion else 'N/A',
                'user_id': d.get('creado_por', 'N/A')  # Ahora es UUID
            })
        return data
    except Exception as e:
        print(f"Error al obtener clientes detallados: {e}")
        return []

def create_cliente(nombre: str, user_id: str) -> Optional[int]:
    """Crea un nuevo cliente. user_id es UUID de Supabase Auth."""
    supabase = get_supabase_client()
    try:
        response = supabase.table("clientes").insert({
            "nombre": nombre,
            "creado_por": user_id  # UUID del usuario de Supabase Auth
        }).execute()
        return response.data[0]['id'] if response.data else None
    except Exception as e:
        print(f"Error al crear cliente: {e}")
        return None

def update_cliente(cliente_id: int, nombre: str, user_id: str) -> bool:
    """Actualiza un cliente existente."""
    supabase = get_supabase_client()
    try:
        # Verificamos que el cliente pertenezca al usuario
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

def get_lugares_trabajo(user_id: Optional[str] = None) -> List[Tuple[int, str]]:
    """Obtiene todos los lugares de trabajo (id, nombre)."""
    supabase = get_supabase_client()
    try:
        query = supabase.table("lugares_trabajo").select("id, nombre").order("nombre")
        if user_id:
            query = query.eq("creado_por", user_id)
            
        response = query.execute()
        return [(d['id'], d['nombre']) for d in response.data]
    except Exception as e:
        print(f"Error al obtener lugares de trabajo: {e}")
        return []

def create_lugar_trabajo(nombre: str, user_id: str) -> Optional[int]:
    """Crea un nuevo lugar de trabajo. user_id es UUID."""
    supabase = get_supabase_client()
    try:
        response = supabase.table("lugares_trabajo").insert({
            "nombre": nombre,
            "creado_por": user_id  # UUID
        }).execute()
        return response.data[0]['id'] if response.data else None
    except Exception as e:
        print(f"Error al crear lugar de trabajo: {e}")
        return None


# ==================== FUNCIONES DE PRESUPUESTOS ====================

def save_presupuesto_completo(user_id, cliente_id, lugar_trabajo_id, descripcion, items_data, total):
    print("📌 save_presupuesto_completo() fue llamada correctamente")
    supabase = get_supabase_client()
    if not user_id:
        print("Usuario no autenticado")
        return {"error": "Usuario no autenticado"}

    try:
        # 1. Insertar el presupuesto general en la tabla "presupuestos"
        response = supabase.table("presupuestos").insert({
            "user_id": user_id,
            "cliente_id": cliente_id,
            "lugar_trabajo_id": lugar_trabajo_id,
            "descripcion": descripcion,
            "total": total
        }).execute()

        if not response.data:
            return {"error": "No se pudo crear el presupuesto"}

        presupuesto_id = response.data[0]["id"]
        print(f"Presupuesto creado con ID: {presupuesto_id}")

        # 2. Guardar los ítems del presupuesto
        print("🔍 Datos structure:", items_data)

        for categoria, data in items_data.items():
            print(f"Procesando categoría: {categoria}")

            # Extraer categoria_id (AHORA SÍ)
            categoria_id = data.get("categoria_id")

            if categoria_id is None:
                print(f"⚠️ ERROR: La categoría '{categoria}' NO tiene categoria_id.")
                continue  # prevenimos errores en supabase

            # Procesar los ítems normales
            for item in data.get('items', []):
                print("Intentando guardar ítem:", item)

                # Revisar si ya existe por ID
                existing_item = supabase.table("items_en_presupuesto") \
                    .select("*") \
                    .eq("presupuesto_id", presupuesto_id) \
                    .eq("id", item.get('id')) \
                    .execute()

                if not existing_item.data:
                    supabase.table("items_en_presupuesto").insert({
                        "presupuesto_id": presupuesto_id,
                        "categoria_id": categoria_id,   # ✔️ CORREGIDO
                        "nombre_personalizado": item.get('nombre_personalizado'),
                        "unidad": item.get('unidad'),
                        "cantidad": item.get('cantidad'),
                        "precio_unitario": item.get('precio_unitario'),
                        "notas": item.get('notas'),
                    }).execute()

            # 3. Guardar mano de obra SI LA CATEGORÍA lo incluye
            if "mano_obra" in data:
                supabase.table("mano_obra").insert({
                    "presupuesto_id": presupuesto_id,
                    "categoria_id": categoria_id,   # ✔️ CORREGIDO
                    "horas": data['mano_obra'].get('horas', 0),
                    "valor_hora": data['mano_obra'].get('valor_hora', 0),
                    "total": data['mano_obra'].get('total', 0)
                }).execute()

        return {"success": True, "presupuesto_id": presupuesto_id}

    except Exception as e:
        print("Error al guardar:", str(e))
        return {"error": str(e)}

def update_presupuesto_detalles(presupuesto_id: int, cliente_id: int, lugar_trabajo_id: int, descripcion: str, total_general: float) -> bool:
    """Actualiza los campos principales del presupuesto."""
    supabase = get_supabase_client()
    try:
        response = supabase.table("presupuestos").update({
            "cliente_id": cliente_id,
            "lugar_trabajo_id": lugar_trabajo_id,
            "descripcion": descripcion,
            "total": float(total_general)
        }).eq("id", presupuesto_id).execute()
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

def save_edited_presupuesto(presupuesto_id: int, user_id: str, cliente_id: int, lugar_trabajo_id: int, descripcion: str, items_data: Dict[str, Any], total_general: float) -> Optional[int]:
    """
    Guarda los cambios de un presupuesto existente.
    """
    supabase = get_supabase_client()
    try:
        # 1. Actualizar el registro principal
        num_items = sum(len(data['items']) for cat, data in items_data.items() if cat != 'general') + (1 if items_data['general'].get('mano_obra', 0) > 0 else 0)
        
        actualizacion_principal = supabase.table("presupuestos").update({
            "cliente_id": cliente_id,
            "lugar_trabajo_id": lugar_trabajo_id,
            "descripcion": descripcion,
            "total": float(total_general),
            "num_items": num_items
        }).eq("id", presupuesto_id).eq("creado_por", user_id).execute()  # Verificar pertenencia con UUID
        
        if not actualizacion_principal.data:
            print(f"Error: No se encontró el presupuesto {presupuesto_id} para actualizar o no tiene permiso.")
            return None
            
        # 2. Eliminar ítems anteriores
        delete_items_presupuesto(presupuesto_id)
        
        # 3. Preparar los ítems para la inserción masiva
        items_to_insert = []
        for categoria, data in items_data.items():
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
            
            for item in data['items']:
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
        presupuesto_response = supabase.table("presupuestos").select(
            "*, cliente:cliente_id(*), lugar:lugar_trabajo_id(*)"
        ).eq("id", presupuesto_id).limit(1).execute()
        
        if not presupuesto_response.data:
            return None
            
        presupuesto = presupuesto_response.data[0]
        
        items_response = supabase.table("items_en_presupuesto").select("*").eq("presupuesto_id", presupuesto_id).order("id").execute()
        
        detalle = {
            "id": presupuesto.get('id'),
            "fecha": presupuesto.get('fecha_creacion'),
            "cliente": presupuesto.get('cliente'),
            "lugar": presupuesto.get('lugar'),
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
        query = supabase.table("presupuestos").select(
            "id, fecha_creacion, total, num_items, cliente:cliente_id(*), lugar:lugar_trabajo_id(*)"
        ).eq("creado_por", user_id)  # UUID del usuario

        # Aplicar filtros
        if 'cliente_id' in filtros and filtros['cliente_id'] is not None:
            query = query.eq("cliente_id", filtros['cliente_id'])
        if 'lugar_trabajo_id' in filtros and filtros['lugar_trabajo_id'] is not None:
            query = query.eq("lugar_trabajo_id", filtros['lugar_trabajo_id'])
        if 'fecha_inicio' in filtros and filtros['fecha_inicio'] is not None:
            query = query.gte("fecha_creacion", filtros['fecha_inicio'].isoformat())

        response = query.order("fecha_creacion", desc=True).execute()

        presupuestos_formateados = []
        for p in response.data:
            fecha_creacion = p.get('fecha_creacion')
            if fecha_creacion and isinstance(fecha_creacion, str):
                try:
                    fecha_obj = datetime.fromisoformat(fecha_creacion.replace('Z', '+00:00'))
                except ValueError:
                    fecha_obj = datetime(1970, 1, 1)
            else:
                fecha_obj = datetime(1970, 1, 1)
                
            presupuestos_formateados.append({
                'id': p['id'],
                'fecha': fecha_obj,
                'total': float(p.get('total', 0)),
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
    """
    supabase = get_supabase_client()
    try:
        # 1. Eliminar ítems asociados
        delete_items_presupuesto(presupuesto_id)

        # 2. Eliminar el presupuesto principal (verificando pertenencia con UUID)
        response = supabase.table("presupuestos").delete().eq("id", presupuesto_id).eq("creado_por", user_id).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error al eliminar presupuesto completo {presupuesto_id}: {e}")
        return False

# ==================== FUNCIONES PARA ITEMS y CATEGORIAS ====================

def get_categorias(user_id: Optional[str] = None) -> List[Tuple[int, str]]:
    """Obtiene todas las categorías existentes (id, nombre)"""
    supabase = get_supabase_client()
    try:
        query = supabase.table("categorias").select("id, nombre").order("nombre")
        if user_id:
            query = query.eq("creado_por", user_id)
            
        response = query.execute()
        return [(d['id'], d['nombre']) for d in response.data]
    except Exception as e:
        print(f"Error al obtener categorias: {e}")
        return []

def create_categoria(nombre: str, user_id: str) -> Optional[int]:
    """Crea una nueva categoría. user_id es UUID."""
    supabase = get_supabase_client()
    try:
        response = supabase.table("categorias").insert({
            "nombre": nombre,
            "creado_por": user_id  # UUID
        }).execute() 
        
        return response.data[0]['id'] if response.data else None
    except Exception as e:
        print(f"Error al crear categoria: {e}")
        return None