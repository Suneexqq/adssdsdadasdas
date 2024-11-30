# handlers/__init__.py
def register_user_handlers(dp):
    from .user import register_user_handlers as ruh
    ruh(dp)

def register_admin_handlers(dp):
    from .admin import register_admin_handlers as rah
    rah(dp)
