"""
数据存储模块 - SQLite 数据库操作（线程连接复用）
"""

import sqlite3
import os
import threading
from datetime import datetime, timedelta
from config import DB_PATH, DATA_DIR, get_config


class Storage:
    """剪贴板数据存储管理"""

    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._lock = threading.Lock()
        self._local = threading.local()
        self._init_db()

    def _get_conn(self):
        """获取线程本地连接（自动复用）"""
        conn = getattr(self._local, 'conn', None)
        if conn is None:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn = conn
        return conn

    def _close_conn(self):
        """关闭当前线程的连接（退出时调用）"""
        conn = getattr(self._local, 'conn', None)
        if conn:
            try:
                conn.close()
            except Exception:
                pass
            self._local.conn = None

    def _init_db(self):
        with self._lock:
            conn = self._get_conn()
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS clipboard_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_type TEXT NOT NULL DEFAULT 'text',
                    text_content TEXT,
                    image_path TEXT,
                    content_hash TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'other_text',
                    subcategory TEXT DEFAULT '',
                    summary TEXT,
                    is_favorite INTEGER DEFAULT 0,
                    use_count INTEGER DEFAULT 0,
                    copy_count INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now','localtime')),
                    last_used_at TEXT,
                    deleted INTEGER DEFAULT 0,
                    deleted_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_category ON clipboard_items(category);
                CREATE INDEX IF NOT EXISTS idx_subcategory ON clipboard_items(subcategory);
                CREATE INDEX IF NOT EXISTS idx_created ON clipboard_items(created_at);
                CREATE INDEX IF NOT EXISTS idx_favorite ON clipboard_items(is_favorite);
                CREATE INDEX IF NOT EXISTS idx_hash ON clipboard_items(content_hash);
                CREATE INDEX IF NOT EXISTS idx_deleted ON clipboard_items(deleted);
                CREATE INDEX IF NOT EXISTS idx_use_count ON clipboard_items(use_count);
                CREATE INDEX IF NOT EXISTS idx_deleted_at ON clipboard_items(deleted_at);
            """)
            # 兼容旧表：添加可能缺失的列
            for col_sql in [
                "ALTER TABLE clipboard_items ADD COLUMN subcategory TEXT DEFAULT ''",
                "ALTER TABLE clipboard_items ADD COLUMN deleted_at TEXT",
            ]:
                try:
                    conn.execute(col_sql)
                except sqlite3.OperationalError:
                    pass  # 列已存在
            conn.commit()

    # ========== 写入 ==========

    def add_item(self, content_type, content_hash, text_content=None,
                 image_path=None, category="other_text", subcategory="",
                 summary=None):
        with self._lock:
            conn = self._get_conn()
            cursor = conn.execute("""
                INSERT INTO clipboard_items
                    (content_type, text_content, image_path, content_hash,
                     category, subcategory, summary, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
            """, (content_type, text_content, image_path, content_hash,
                  category, subcategory, summary))
            conn.commit()
            return cursor.lastrowid

    def get_item_by_id(self, item_id):
        """通过 ID 精确查询单条记录"""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM clipboard_items WHERE id=? LIMIT 1", (item_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_item_by_hash(self, content_hash):
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM clipboard_items WHERE content_hash=? AND deleted=0 ORDER BY created_at DESC LIMIT 1",
            (content_hash,))
        return row.fetchone()

    def update_copy(self, item_id):
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                "UPDATE clipboard_items SET copy_count=copy_count+1, last_used_at=datetime('now','localtime') WHERE id=?",
                (item_id,))
            conn.commit()

    def mark_used(self, item_id):
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                "UPDATE clipboard_items SET use_count=use_count+1, last_used_at=datetime('now','localtime') WHERE id=?",
                (item_id,))
            conn.commit()

    def set_category(self, item_id, category):
        with self._lock:
            conn = self._get_conn()
            conn.execute("UPDATE clipboard_items SET category=? WHERE id=?", (category, item_id))
            conn.commit()

    def set_subcategory(self, item_id, subcategory):
        with self._lock:
            conn = self._get_conn()
            conn.execute("UPDATE clipboard_items SET subcategory=? WHERE id=?", (subcategory, item_id))
            conn.commit()

    def toggle_favorite(self, item_id):
        with self._lock:
            conn = self._get_conn()
            row = conn.execute("SELECT is_favorite FROM clipboard_items WHERE id=?", (item_id,)).fetchone()
            if row:
                new = 0 if row["is_favorite"] else 1
                conn.execute("UPDATE clipboard_items SET is_favorite=? WHERE id=?", (new, item_id))
                conn.commit()
                return bool(new)
            return False

    def update_summary(self, item_id, summary):
        with self._lock:
            conn = self._get_conn()
            conn.execute("UPDATE clipboard_items SET summary=? WHERE id=?", (summary, item_id))
            conn.commit()

    # ========== 软删除 ==========

    def _ensure_list(self, item_ids):
        return [item_ids] if isinstance(item_ids, int) else list(item_ids)

    def soft_delete(self, item_ids):
        item_ids = self._ensure_list(item_ids)
        if not item_ids:
            return
        with self._lock:
            conn = self._get_conn()
            ph = ",".join("?" * len(item_ids))
            conn.execute(
                f"UPDATE clipboard_items SET deleted=1, deleted_at=datetime('now','localtime') WHERE id IN ({ph})",
                item_ids)
            conn.commit()

    def restore_items(self, item_ids):
        item_ids = self._ensure_list(item_ids)
        if not item_ids:
            return
        with self._lock:
            conn = self._get_conn()
            ph = ",".join("?" * len(item_ids))
            conn.execute(f"UPDATE clipboard_items SET deleted=0, deleted_at=NULL WHERE id IN ({ph})", item_ids)
            conn.commit()

    def hard_delete(self, item_ids):
        item_ids = self._ensure_list(item_ids)
        if not item_ids:
            return
        with self._lock:
            conn = self._get_conn()
            ph = ",".join("?" * len(item_ids))
            conn.execute(f"DELETE FROM clipboard_items WHERE id IN ({ph})", item_ids)
            conn.commit()

    def purge_expired_deleted(self, days=7):
        """清除已删除超过 N 天的条目"""
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            conn = self._get_conn()
            cur = conn.execute("DELETE FROM clipboard_items WHERE deleted=1 AND deleted_at < ?", (cutoff,))
            n = cur.rowcount
            conn.commit()
            return n

    def clear_all_deleted(self):
        """清空所有已删除条目"""
        with self._lock:
            conn = self._get_conn()
            cur = conn.execute("DELETE FROM clipboard_items WHERE deleted=1")
            n = cur.rowcount
            conn.commit()
            return n

    # ========== 查询（DRY WHERE 构建）==========

    def _build_where(self, category=None, subcategory=None, search=None, tab="recent"):
        """构建查询条件和参数，避免 get_items / get_item_count 重复逻辑"""
        conditions = []
        params = []

        if tab == "deleted":
            conditions.append("deleted = 1")
        else:
            conditions.append("deleted = 0")
            if tab == "favorite":
                conditions.append("is_favorite = 1")
            elif category:
                conditions.append("category = ?")
                params.append(category)
                if subcategory:
                    conditions.append("subcategory = ?")
                    params.append(subcategory)

        if search:
            conditions.append("(text_content LIKE ? OR summary LIKE ?)")
            p = f"%{search}%"
            params.extend([p, p])

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        return where, params

    def get_items(self, category=None, subcategory=None, search=None,
                  limit=200, offset=0, include_favorites=None, tab="recent"):
        conn = self._get_conn()
        where, params = self._build_where(category, subcategory, search, tab)

        order = "ORDER BY deleted_at DESC" if tab == "deleted" else "ORDER BY created_at DESC"

        rows = conn.execute(
            f"SELECT * FROM clipboard_items {where} {order} LIMIT ? OFFSET ?",
            params + [int(limit), int(offset)]
        ).fetchall()
        return [dict(r) for r in rows]

    def get_item_count(self, category=None, subcategory=None, search=None, tab="recent"):
        conn = self._get_conn()
        where, params = self._build_where(category, subcategory, search, tab)
        row = conn.execute(f"SELECT COUNT(*) as cnt FROM clipboard_items {where}", params).fetchone()
        return row["cnt"] if row else 0

    def get_items_sorted(self, sort_by="use_count", category=None, include_favorites=True, limit=None):
        conn = self._get_conn()
        conditions = ["deleted = 0"]
        params = []
        if category and category != "all":
            if category == "favorite":
                conditions.append("is_favorite = 1")
            else:
                conditions.append("category = ?")
                params.append(category)
        if not include_favorites:
            conditions.append("is_favorite = 0")
        where = "WHERE " + " AND ".join(conditions)
        sort_map = {
            "use_count": "use_count ASC",
            "created_at": "created_at DESC",
            "copy_count": "copy_count DESC",
            "use_count_desc": "use_count DESC",
            "created_at_asc": "created_at ASC"
        }
        order = sort_map.get(sort_by, "use_count ASC")
        lc = f"LIMIT {int(limit)}" if limit else ""
        rows = conn.execute(f"SELECT * FROM clipboard_items {where} ORDER BY {order} {lc}", params).fetchall()
        return [dict(r) for r in rows]

    def cleanup_old_items(self, max_history=None):
        if max_history is None:
            max_history = get_config("max_history", 500)
        with self._lock:
            conn = self._get_conn()
            cur = conn.execute("""
                DELETE FROM clipboard_items WHERE id IN (
                    SELECT id FROM clipboard_items
                    WHERE deleted=0 AND is_favorite=0
                    ORDER BY created_at DESC LIMIT -1 OFFSET ?
                )
            """, (max_history,))
            n = cur.rowcount
            conn.commit()
            return n

    def close(self):
        """关闭当前线程的数据库连接（退出时调用）"""
        self._close_conn()

    def get_storage_size(self):
        """获取数据库和图片占用的总字节数"""
        total = 0
        if os.path.exists(DB_PATH):
            total += os.path.getsize(DB_PATH)
        if os.path.exists(IMAGES_DIR):
            for root, dirs, files in os.walk(IMAGES_DIR):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        total += os.path.getsize(fp)
                    except OSError:
                        pass
        return total


_storage_instance = None


def get_storage():
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = Storage()
    return _storage_instance
