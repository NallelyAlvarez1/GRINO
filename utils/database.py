import psycopg2
from dotenv import load_dotenv
import os
import bcrypt
import uuid
from typing import List, Tuple, Optional, Dict, Any

# Cargar variables de entorno
load_dotenv()

# ==================== FUNCIONES DE AUTENTICACIÓN ====================
def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def check_login(username: str, password: str) -> Dict[str, Any]:
    """Verifica credenciales de usuario"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, password_hash, es_admin FROM usuarios WHERE username = %s", (username,))
            user_data = cur.fetchone()
        
        if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data[1].encode('utf-8')):
            return {"success": True, "user_id": user_data[0], "is_admin": user_data[2]}
        return {"success": False}
    finally:
        conn.close()

# ==================== FUNCIONES DE CLIENTES ====================
def get_clientes() -> List[Tuple[int, str]]:
    """Obtiene todos los clientes (id, nombre)"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nombre FROM clientes ORDER BY nombre")
            return cur.fetchall()
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
def create_presupuesto(cliente_id: int, lugar_trabajo_nombre: str, user_id: int) -> Optional[int]:
    """Crea un nuevo presupuesto vacío"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO presupuestos 
                (cliente_id, lugar_trabajo, total, ruta_pdf, creado_por) 
                VALUES (%s, %s, 0, '', %s) RETURNING id""",
                (cliente_id, lugar_trabajo_nombre, user_id)
            )
            conn.commit()
            return cur.fetchone()[0]
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
            # Obtener datos básicos del presupuesto
            cur.execute(
                """SELECT p.id, p.fecha_creacion, p.total, p.notas,
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

            # Obtener items del presupuesto
            cur.execute(
                """SELECT i.nombre_personalizado, i.unidad, i.cantidad, 
                      i.precio_unitario, i.total, i.notas,
                      cat.nombre AS categoria
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
                'cliente': {'id': presupuesto[4], 'nombre': presupuesto[5]},
                'lugar': {'id': presupuesto[6], 'nombre': presupuesto[7]},
                'items': [{
                    'nombre': item[0],
                    'unidad': item[1],
                    'cantidad': item[2],
                    'precio_unitario': item[3],
                    'total': item[4],
                    'notas': item[5],
                    'categoria': item[6]
                } for item in items]
            }
    finally:
        conn.close()

def get_presupuestos_usuario(user_id: int, filtros: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Obtiene todos los presupuestos del usuario con opción de filtrado"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            query = """
                SELECT p.id, p.fecha_creacion, p.total, p.notas,
                       c.id AS cliente_id, c.nombre AS cliente_nombre,
                       l.id AS lugar_id, l.nombre AS lugar_nombre
                FROM presupuestos p
                JOIN clientes c ON p.cliente_id = c.id
                JOIN lugares_trabajo l ON p.lugar_trabajo_id = l.id
                WHERE p.creado_por = %s
            """
            params = [user_id]

            # Aplicar filtros si existen
            if filtros:
                if filtros.get('cliente_id'):
                    query += " AND p.cliente_id = %s"
                    params.append(filtros['cliente_id'])
                if filtros.get('lugar_id'):
                    query += " AND p.lugar_trabajo_id = %s"
                    params.append(filtros['lugar_id'])
                if filtros.get('fecha_inicio'):
                    query += " AND p.fecha_creacion >= %s"
                    params.append(filtros['fecha_inicio'])
                if filtros.get('fecha_fin'):
                    query += " AND p.fecha_creacion <= %s"
                    params.append(filtros['fecha_fin'])
                if filtros.get('search'):
                    search = f"%{filtros['search']}%"
                    query += " AND (c.nombre ILIKE %s OR l.nombre ILIKE %s OR p.notas ILIKE %s)"
                    params.extend([search, search, search])

            query += " ORDER BY p.fecha_creacion DESC"
            
            cur.execute(query, params)
            resultados = cur.fetchall()

            return [{
                'id': row[0],
                'fecha': row[1],
                'total': row[2],
                'notas': row[3],
                'cliente': {'id': row[4], 'nombre': row[5]},
                'lugar': {'id': row[6], 'nombre': row[7]},
                'num_items': contar_items_presupuesto(row[0])  # Función adicional
            } for row in resultados]
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

def get_presupuestos_por_cliente(cliente_id: int) -> List[Dict[str, Any]]:
    """Obtiene todos los presupuestos para un cliente específico"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT p.id, p.fecha_creacion, p.total, l.nombre AS lugar
                   FROM presupuestos p
                   JOIN lugares_trabajo l ON p.lugar_trabajo_id = l.id
                   WHERE p.cliente_id = %s
                   ORDER BY p.fecha_creacion DESC""",
                (cliente_id,)
            )
            return [{
                'id': row[0],
                'fecha': row[1],
                'total': row[2],
                'lugar': row[3]
            } for row in cur.fetchall()]
    finally:
        conn.close()

def get_presupuestos_por_lugar(lugar_id: int) -> List[Dict[str, Any]]:
    """Obtiene todos los presupuestos para un lugar específico"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT p.id, p.fecha_creacion, p.total, c.nombre AS cliente
                   FROM presupuestos p
                   JOIN clientes c ON p.cliente_id = c.id
                   WHERE p.lugar_trabajo_id = %s
                   ORDER BY p.fecha_creacion DESC""",
                (lugar_id,)
            )
            return [{
                'id': row[0],
                'fecha': row[1],
                'total': row[2],
                'cliente': row[3]
            } for row in cur.fetchall()]
    finally:
        conn.close()

def save_presupuesto_completo(presupuesto_id: int, items_data: Dict[str, Any]) -> bool:
    """Guarda todos los items de un presupuesto en la base de datos"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Eliminar items existentes para este presupuesto
            cur.execute("DELETE FROM items_en_presupuesto WHERE presupuesto_id = %s", (presupuesto_id,))
            
            # Insertar nuevos items
            for categoria, data in items_data.items():
                # Insertar mano de obra como un item especial
                if data['mano_obra'] > 0:
                    cur.execute(
                        """INSERT INTO items_en_presupuesto 
                        (presupuesto_id, categoria_id, nombre_personalizado, unidad, cantidad, precio_unitario, notas)
                        VALUES (%s, (SELECT id FROM categorias WHERE nombre = %s), 'Mano de Obra', 'Unidad', 1, %s, 'Mano de obra')""",
                        (presupuesto_id, categoria, data['mano_obra'])
                    )
                
                # Insertar items normales
                for item in data['items']:
                    cur.execute(
                        """INSERT INTO items_en_presupuesto 
                        (presupuesto_id, categoria_id, nombre_personalizado, unidad, cantidad, precio_unitario)
                        VALUES (%s, (SELECT id FROM categorias WHERE nombre = %s), %s, %s, %s, %s)""",
                        (presupuesto_id, categoria, item['nombre'], item['unidad'], item['cantidad'], item['precio_unitario']))
            
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ==================== FUNCIONES PARA ITEMS y CATEGORIAS ====================
def get_items_base() -> List[Tuple[int, str, str, float]]:
    """Obtiene todos los items base (id, nombre, unidad, precio_referencia)"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nombre, unidad, precio_referencia FROM items_base ORDER BY nombre")
            return cur.fetchall()
    finally:
        conn.close()

def create_item_base(categoria_id: int, nombre: str, unidad: str, precio: float) -> int:
    """Crea un nuevo item base"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO items_base (categoria_id, nombre, unidad, precio_referencia) VALUES (%s, %s, %s, %s) RETURNING id",
                (categoria_id, nombre, unidad, precio)
            )
            conn.commit()
            return cur.fetchone()[0]
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_categorias() -> List[Tuple[int, str]]:
    """Obtiene todas las categorías existentes (id, nombre)"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nombre FROM categorias ORDER BY nombre")
            return cur.fetchall()
    finally:
        conn.close()

def create_categoria(nombre: str) -> int:
    """Crea una nueva categoría y retorna su ID"""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO categorias (nombre) VALUES (%s) RETURNING id",
                (nombre,)
            )
            conn.commit()
            return cur.fetchone()[0]
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

#nuevos
