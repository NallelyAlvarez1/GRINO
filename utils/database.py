import psycopg2
from dotenv import load_dotenv
import os
import bcrypt
import uuid
from typing import List, Tuple, Optional, Dict, Any

load_dotenv()

# ==================== FUNCIONES DE AUTENTICACIÓN ====================
def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

# ==================== FUNCIONES DE CLIENTES ====================
def get_clientes() -> List[Tuple[int, str]]:
    """Obtiene todos los clientes - para presupuesto"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nombre FROM clientes ORDER BY nombre")
            return cur.fetchall()
    finally:
        conn.close()

def get_clientes_detallados(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Obtiene clientes con más detalles - gestión de clientes
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            if user_id:
                cur.execute("""
                    SELECT id, nombre, fecha_registro, creado_por 
                    FROM clientes 
                    WHERE creado_por = %s 
                    ORDER BY nombre
                """, (user_id,))
            else:
                cur.execute("""
                    SELECT id, nombre, fecha_registro, creado_por 
                    FROM clientes 
                    ORDER BY nombre
                """)
            
            return [{
                'id': row[0],
                'nombre': row[1],
                'fecha_registro': row[2],
                'creado_por': row[3]
            } for row in cur.fetchall()]
    finally:
        conn.close()

def create_cliente(nombre: str, user_id: int) -> Optional[int]:
    """Crea un nuevo cliente con alias único"""
    alias = f"{nombre.lower().replace(' ', '-')}-{str(uuid.uuid4())[:4]}"
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO clientes (nombre, alias, creado_por) VALUES (%s, %s, %s) RETURNING id",
                (nombre, alias, user_id)
            )
            conn.commit()
            return cur.fetchone()[0]
    except Exception as e:
        print(f"Error al crear cliente: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def update_cliente(cliente_id: int, nombre: str, user_id: int) -> bool:
    """
    Actualiza los datos de un cliente existente
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Verificar que el cliente pertenece al usuario antes de editar
            cur.execute("""
                UPDATE clientes 
                SET nombre = %s 
                WHERE id = %s AND creado_por = %s
            """, (nombre, cliente_id, user_id))
            conn.commit()
            return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_cliente(cliente_id: int, user_id: int) -> bool:
    """
    Elimina un cliente de la base de datos
    
    Args:
        cliente_id: ID del cliente a eliminar
        user_id: ID del usuario que realiza la eliminación
    
    Returns:
        True si la eliminación fue exitosa, False si no
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Verificar que el cliente pertenece al usuario antes de eliminar
            cur.execute("""
                DELETE FROM clientes 
                WHERE id = %s AND creado_por = %s
            """, (cliente_id, user_id))
            conn.commit()
            return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ==================== FUNCIONES DE LUGARES DE TRABAJO ====================
def get_lugares_trabajo() -> List[Tuple[int, str]]:
    """Obtiene todos los lugares de trabajo (id, nombre)"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nombre FROM lugares_trabajo ORDER BY nombre")
            return cur.fetchall()
    finally:
        conn.close()

def create_lugar_trabajo(nombre: str, user_id: int) -> Optional[int]:
    """Crea un nuevo lugar de trabajo"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO lugares_trabajo (nombre, creado_por) VALUES (%s, %s) RETURNING id",
                (nombre, user_id)
            )
            conn.commit()
            return cur.fetchone()[0]
    except Exception as e:
        print(f"Error al crear lugar de trabajo: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

# ==================== FUNCIONES PARA PRESUPUESTOS ====================
def create_presupuesto(cliente_id: int, lugar_id: int, descripcion: str, total: float, user_id: int) -> Optional[int]:
    """Crea un nuevo presupuesto y retorna su ID"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO presupuestos 
                (cliente_id, lugar_trabajo_id, fecha_creacion, descripcion, total, creado_por)
                VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s, %s) 
                RETURNING id
                """,
                (cliente_id, lugar_id, descripcion, total, user_id)
            )
            presupuesto_id = cur.fetchone()[0]
            conn.commit()
            return presupuesto_id
    except Exception as e:
        print(f"Error al crear presupuesto: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_presupuesto_detallado(presupuesto_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene todos los datos de un presupuesto específico incluyendo items"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT p.id, p.fecha_creacion, p.total, p.notas, p.descripcion,
                    c.id AS cliente_id, c.nombre AS cliente_nombre,
                    l.id AS lugar_id, l.nombre AS lugar_nombre
                FROM presupuestos p
                JOIN clientes c ON p.cliente_id = c.id
                JOIN lugares_trabajo l ON p.lugar_trabajo_id = l.id
                WHERE p.id = %s""",
                (presupuesto_id,)
            )

            presupuesto = cur.fetchone()
            if not presupuesto:
                return None

            cur.execute(
                """SELECT i.nombre_personalizado, i.unidad, i.cantidad, 
                      i.precio_unitario, i.total, i.notas,
                      cat.nombre AS categoria,
                      i.categoria_id AS categoria_id
                   FROM items_en_presupuesto i
                   LEFT JOIN categorias cat ON i.categoria_id = cat.id
                   WHERE i.presupuesto_id = %s""",
                (presupuesto_id,)
            )
            items = cur.fetchall()

            return {
                'id': presupuesto[0],
                'fecha': presupuesto[1],
                'total': presupuesto[2],
                'notas': presupuesto[3],
                'descripcion': presupuesto[4],
                'cliente': {'id': presupuesto[5], 'nombre': presupuesto[6]},
                'lugar': {'id': presupuesto[7], 'nombre': presupuesto[8]},
                'items': [{
                    'nombre': item[0],
                    'unidad': item[1],
                    'cantidad': item[2],
                    'precio_unitario': item[3],
                    'total': item[4],
                    'notas': item[5],
                    'categoria': item[6],
                    'categoria_id': item[7]
                } for item in items]
            }
    finally:
        conn.close()

def get_presupuestos_usuario(user_id: int, filtros: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Obtiene presupuestos con filtros avanzados"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            base_query = """
                SELECT p.id, p.fecha_creacion, p.total, p.notas,
                       c.id AS cliente_id, c.nombre AS cliente_nombre,
                       l.id AS lugar_id, l.nombre AS lugar_nombre
                FROM presupuestos p
                JOIN clientes c ON p.cliente_id = c.id
                JOIN lugares_trabajo l ON p.lugar_trabajo_id = l.id
                WHERE p.creado_por = %s
            """
            params = [user_id]
            
            query_parts = [base_query]
            
            if filtros:
                if filtros.get('cliente_id'):
                    query_parts.append(" AND p.cliente_id = %s")
                    params.append(filtros['cliente_id'])
                
                if filtros.get('lugar_id'):
                    query_parts.append(" AND p.lugar_trabajo_id = %s")
                    params.append(filtros['lugar_id'])
                
                if filtros.get('fecha_inicio'):
                    query_parts.append(" AND p.fecha_creacion >= %s")
                    params.append(filtros['fecha_inicio'])
                
                if filtros.get('fecha_fin'):
                    query_parts.append(" AND p.fecha_creacion <= %s")
                    params.append(filtros['fecha_fin'])
                
                if filtros.get('search'):
                    search = f"%{filtros['search']}%"
                    query_parts.append(" AND (c.nombre ILIKE %s OR l.nombre ILIKE %s OR p.notas ILIKE %s)")
                    params.extend([search, search, search])
            
            query_parts.append(" ORDER BY p.fecha_creacion DESC")
            
            final_query = "".join(query_parts)
            cur.execute(final_query, params)
            
            return [{
                'id': row[0],
                'fecha': row[1],
                'total': row[2],
                'notas': row[3],
                'cliente': {'id': row[4], 'nombre': row[5]},
                'lugar': {'id': row[6], 'nombre': row[7]},
                'num_items': contar_items_presupuesto(row[0])
            } for row in cur.fetchall()]
            
    except Exception as e:
        print(f"Error al obtener presupuestos: {e}")
        return []
    finally:
        conn.close()

def contar_items_presupuesto(presupuesto_id: int) -> int:
    """Cuenta los items asociados a un presupuesto"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM items_en_presupuesto WHERE presupuesto_id = %s",
                (presupuesto_id,)
            )
            return cur.fetchone()[0]
    finally:
        conn.close()

def save_presupuesto_completo(presupuesto_id: int, items_data: Dict[str, Any]) -> bool:
    """Guarda todos los items de un presupuesto en la base de datos"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM items_en_presupuesto WHERE presupuesto_id = %s", (presupuesto_id,))
            
            for categoria, data in items_data.items():
                if data.get('mano_obra', 0) > 0:
                    cur.execute(
                        """INSERT INTO items_en_presupuesto 
                        (presupuesto_id, categoria_id, nombre_personalizado, unidad, cantidad, precio_unitario, notas)
                        VALUES (%s, (SELECT id FROM categorias WHERE nombre = %s), 'Mano de Obra', 'Unidad', 1, %s, 'Mano de obra')""",
                        (presupuesto_id, categoria, data['mano_obra'])
                    )
                
                for item in data['items']:
                    cur.execute(
                        """INSERT INTO items_en_presupuesto 
                        (presupuesto_id, categoria_id, nombre_personalizado, unidad, cantidad, precio_unitario, notas)
                        VALUES (%s, (SELECT id FROM categorias WHERE nombre = %s), %s, %s, %s, %s, %s)""",
                        (presupuesto_id, categoria, item['nombre'], item['unidad'], item['cantidad'], item['precio_unitario'], item.get('notas', '')))
            
            cur.execute(
                """UPDATE presupuestos SET total = (
                    SELECT COALESCE(SUM(total), 0) 
                    FROM items_en_presupuesto 
                    WHERE presupuesto_id = %s
                ) WHERE id = %s""",
                (presupuesto_id, presupuesto_id)
            )
            
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        print(f"Error al guardar presupuesto completo: {e}")
        return False
    finally:
        conn.close()

def delete_presupuesto(presupuesto_id: int, cliente_id: int) -> bool:
    """
    Elimina un presupuesto de la base de datos

    Args:
        presupuesto_id: ID del presupuesto a eliminar
        user_id: ID del usuario que realiza la eliminación

    Returns:
        True si la eliminación fue exitosa, False si no
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Verificar que el presupuesto pertenece al usuario antes de eliminar
            cur.execute("""
                DELETE FROM presupuestos 
                WHERE id = %s AND creado_por = %s
            """, (presupuesto_id, cliente_id))
            conn.commit()
            return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"Error al eliminar presupuesto: {e}")
        return False
    finally:
        conn.close()
# Función auxiliar para obtener el ID de la categoría (necesario para items_en_presupuesto)
def save_edited_presupuesto(
    cliente_id: int, 
    lugar_id: int, 
    descripcion_original: str, 
    total: float, 
    user_id: int, 
    items_data: List[Dict[str, Any]]
) -> Optional[int]:
    """Crea un nuevo presupuesto como versión editada de uno existente."""
    
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # 1. Crear la cabecera del nuevo presupuesto
            nueva_descripcion = descripcion_original # CORRECCIÓN: Usar f-string en lugar de {}
            
            cur.execute(
                """
                INSERT INTO presupuestos 
                (cliente_id, lugar_trabajo_id, fecha_creacion, descripcion, total, creado_por)
                VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s, %s) 
                RETURNING id
                """,
                (cliente_id, lugar_id, nueva_descripcion, total, user_id)
            )
            nuevo_presupuesto_id = cur.fetchone()[0]
            
            # 2. Guardar los items asociados al nuevo presupuesto
            for item in items_data:
                # Asegurarnos de que los valores numéricos sean float
                cantidad = float(item.get('cantidad', 0))
                precio_unitario = float(item.get('precio_unitario', 0))
                total_item = float(item.get('total', 0))
                
                cur.execute(
                    """
                    INSERT INTO items_en_presupuesto 
                    (presupuesto_id, categoria_id, nombre_personalizado, unidad, cantidad, precio_unitario, notas)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        nuevo_presupuesto_id,
                        item.get('categoria_id'),
                        item.get('nombre_personalizado', ''),
                        item.get('unidad', 'Unidad'),
                        cantidad,
                        precio_unitario,
                        item.get('descripcion', '')
                    )
                )
            
            conn.commit()
            return nuevo_presupuesto_id
            
    except Exception as e:
        print(f"Error al guardar presupuesto editado: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()
# ==================== FUNCIONES PARA ITEMS y CATEGORIAS ====================
def get_categorias() -> List[Tuple[int, str]]:
    """Obtiene todas las categorías existentes (id, nombre)"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nombre FROM categorias ORDER BY nombre")
            return cur.fetchall()
    finally:
        conn.close()

def create_categoria(nombre: str, user_id: int) -> Optional[int]:
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO categorias (nombre, creado_por) VALUES (%s, %s) RETURNING id",
                (nombre, user_id)
            ) 
            conn.commit() 
            new_id = cur.fetchone()[0]            
            return new_id
    except Exception as e:
        print(f"Error al crear categoria: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()


#nuevos
