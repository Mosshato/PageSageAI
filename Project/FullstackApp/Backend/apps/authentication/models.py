"""
User si UserManager raman definite in api.models (tabelul DB e api_user,
migrarile existente depind de el). Le re-exportam aici ca authentication
sa fie punctul de import canonic pentru orice cod nou legat de auth,
fara sa miscam tabelul si fara migrari noi.
"""
from api.models import User, UserManager  # noqa: F401
