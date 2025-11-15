from typing import List, Tuple, Optional, Dict, Any
import streamlit as st
from supabase import Client

# Importar conexión
try:
    from utils.db import get_supabase_client
except ImportError:
    st.error("Error: Falta el archivo 'utils/db.py' con la función get_supabase_client.")
    st.stop()

# ==================== FUNCIONES SIMPLIFICADAS ====================

def get_clientes(user_id: str) -> List[Tuple[int, str]]:
    """Obtiene todos los clientes (id, nombre)"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("clientes").select("id, nombre").eq("creado_por", user_id).order("nombre").execute()
        return [(d['id'], d['nombre']) for d in response.data]
    except Exception as e:
        st.error(f"❌ Error al obtener clientes: {e}")
        return []

def create_cliente(nombre: str, user_id: str) -> Optional[int]:
    """Crea un nuevo cliente"""
    supabase = get_supabase_client()
    try:
        # Crear alias único simple
        import uuid
        alias = f"{nombre.lower().replace(' ', '-')}-{str(uuid.uuid4())[:8]}"
        
        response = supabase.table("clientes").insert({
            "nombre": nombre,
            "alias": alias,
            "creado_por": user_id
        }).execute()
        
        if response.data:
            return response.data[0]['id']
        return None
    except Exception as e:
        st.error(f"❌ Error al crear cliente: {e}")
        return None

def get_lugares_trabajo(user_id: str) -> List[Tuple[int, str]]:
    """Obtiene todos los lugares de trabajo (id, nombre)"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("lugares_trabajo").select("id, nombre").eq("creado_por", user_id).order("nombre").execute()
        return [(d['id'], d['nombre']) for d in response.data]
    except Exception as e:
        st.error(f"❌ Error al obtener lugares de trabajo: {e}")
        return []

def create_lugar_trabajo(nombre: str, user_id: str) -> Optional[int]:
    """Crea un nuevo lugar de trabajo"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("lugares_trabajo").insert({
            "nombre": nombre,
            "creado_por": user_id
        }).execute()
        if response.data:
            return response.data[0]['id']
        return None
    except Exception as e:
        st.error(f"❌ Error al crear lugar de trabajo: {e}")
        return None

def get_categorias(user_id: str) -> List[Tuple[int, str]]:
    """Obtiene todas las categorías existentes (id, nombre)"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("categorias").select("id, nombre").eq("creado_por", user_id).order("nombre").execute()
        return [(d['id'], d['nombre']) for d in response.data]
    except Exception as e:
        st.error(f"❌ Error al obtener categorias: {e}")
        return []

def create_categoria(nombre: str, user_id: str) -> Optional[int]:
    """Crea una nueva categoría"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("categorias").insert({
            "nombre": nombre,
            "creado_por": user_id
        }).execute()
        if response.data:
            return response.data[0]['id']
        return None
    except Exception as e:
        st.error(f"❌ Error al crear categoria: {e}")
        return None

# ==================== FUNCIÓN PRINCIPAL PARA GUARDAR PRESUPUESTO ====================

def save_presupuesto_completo(user_id: str, cliente_id: int, lugar_trabajo_id: int, descripcion: str, items_data: Dict[str, Any], total: float) -> Optional[int]:
    """Guarda el presupuesto completo en la base de datos - VERSIÓN MEJORADA"""
    supabase = get_supabase_client()
    
    try:
        # 1. Crear el presupuesto principal
        presupuesto_response = supabase.table("presupuestos").insert({
            "creado_por": user_id,
            "cliente_id": cliente_id,
            "lugar_trabajo_id": lugar_trabajo_id,
            "descripcion": descripcion,
            "total": total
        }).execute()

        if not presupuesto_response.data:
            st.error("❌ No se pudo crear el presupuesto principal")
            return None

        presupuesto_id = presupuesto_response.data[0]["id"]
        st.success(f"✅ Presupuesto principal creado con ID: {presupuesto_id}")

        # 2. Preparar todos los items para insertar
        items_to_insert = []
        
        for categoria_nombre, data in items_data.items():
            # 🔥 MEJOR DEPURACIÓN
            categoria_id = data.get('categoria_id')
            st.write(f"🔍 Procesando categoría: {categoria_nombre}, ID: {categoria_id}")
            
            if not categoria_id:
                st.warning(f"⚠️ Saltando categoría '{categoria_nombre}' - sin ID")
                continue

            # Insertar mano de obra como item especial
            mano_obra = data.get('mano_obra', 0)
            if mano_obra > 0:
                items_to_insert.append({
                    "presupuesto_id": presupuesto_id,
                    "categoria_id": categoria_id,
                    "nombre_personalizado": f"Mano de Obra - {categoria_nombre}",
                    "unidad": "Servicio",
                    "cantidad": 1,
                    "precio_unitario": mano_obra,
                    "total": mano_obra,
                    "notas": f"Mano de obra para {categoria_nombre}"
                })

            # Insertar items normales
            for item in data.get('items', []):
                items_to_insert.append({
                    "presupuesto_id": presupuesto_id,
                    "categoria_id": categoria_id,
                    "nombre_personalizado": item.get('nombre', ''),
                    "unidad": item.get('unidad', 'Unidad'),
                    "cantidad": item.get('cantidad', 0),
                    "precio_unitario": item.get('precio_unitario', 0),
                    "total": item.get('total', 0),
                    "notas": item.get('notas', '')
                })

        # 3. Insertar todos los items en lote
        if items_to_insert:
            items_response = supabase.table("items_en_presupuesto").insert(items_to_insert).execute()
            st.success(f"✅ {len(items_to_insert)} items guardados para el presupuesto {presupuesto_id}")
            
            # 🔥 VERIFICACIÓN EXTRA
            st.write(f"📦 Items a guardar: {len(items_to_insert)}")
            for item in items_to_insert[:3]:  # Mostrar primeros 3 para verificación
                st.write(f"  - {item['nombre_personalizado']} (Cat ID: {item['categoria_id']})")
        else:
            st.warning("⚠️ No hay items para guardar")

        return presupuesto_id

    except Exception as e:
        st.error(f"❌ Error al guardar presupuesto completo: {str(e)}")
        st.exception(e)  # 🔥 MOSTRAR TRAZA COMPLETA
        return None

# ==================== FUNCIONES PARA CONSULTAS ====================

def get_presupuesto_detallado(presupuesto_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene todos los detalles de un presupuesto"""
    supabase = get_supabase_client()
    try:
        # Obtener datos básicos del presupuesto
        presupuesto_response = supabase.table("presupuestos").select(
            "*, cliente:cliente_id(*), lugar:lugar_trabajo_id(*)"
        ).eq("id", presupuesto_id).execute()

        if not presupuesto_response.data:
            return None

        presupuesto = presupuesto_response.data[0]

        # Obtener items del presupuesto
        items_response = supabase.table("items_en_presupuesto").select(
            "*, categoria:categoria_id(nombre)"
        ).eq("presupuesto_id", presupuesto_id).execute()

        return {
            "id": presupuesto['id'],
            "fecha": presupuesto.get('fecha_creacion'),
            "total": presupuesto.get('total', 0),
            "descripcion": presupuesto.get('descripcion', ''),
            "cliente": presupuesto.get('cliente', {}),
            "lugar": presupuesto.get('lugar', {}),
            "items": items_response.data if items_response.data else []
        }

    except Exception as e:
        st.error(f"❌ Error al obtener presupuesto {presupuesto_id}: {e}")
        return None

def get_presupuestos_usuario(user_id: str) -> List[Dict[str, Any]]:
    """Obtiene todos los presupuestos del usuario"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("presupuestos").select(
            "id, fecha_creacion, total, descripcion, cliente:cliente_id(nombre), lugar:lugar_trabajo_id(nombre)"
        ).eq("creado_por", user_id).order("fecha_creacion", desc=True).execute()

        return response.data if response.data else []

    except Exception as e:
        st.error(f"❌ Error al obtener presupuestos: {e}")
        return []

def delete_presupuesto(presupuesto_id: int, user_id: str) -> bool:
    """Elimina un presupuesto y sus items"""
    supabase = get_supabase_client()
    try:
        # Eliminar items primero
        supabase.table("items_en_presupuesto").delete().eq("presupuesto_id", presupuesto_id).execute()
        
        # Eliminar presupuesto
        response = supabase.table("presupuestos").delete().eq("id", presupuesto_id).eq("creado_por", user_id).execute()
        return len(response.data) > 0
    except Exception as e:
        st.error(f"❌ Error al eliminar presupuesto: {e}")
        return False
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