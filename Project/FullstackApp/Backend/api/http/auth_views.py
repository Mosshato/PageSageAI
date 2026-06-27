"""Authentication endpoints - signup, login, me."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()


def user_payload(user):
    """Formatarea datelor userului care merg in response catre frontend."""
    return {
        'id': user.id,
        'firstName': user.first_name,
        'lastName': user.last_name,
        'email': user.email,
        'role': user.role,
    }


def tokens_for_user(user):
    """
    Genereaza o pereche de token-uri (access + refresh) pentru un user.
    RefreshToken.for_user() din simplejwt creeaza token-urile si
    embedeaza automat user_id in payload.
    Noi adaugam si 'role' in payload — util daca frontend-ul vrea sa il
    decodeze fara un request suplimentar.
    """
    refresh = RefreshToken.for_user(user)
    refresh['role'] = user.role          # camp extra in payload JWT
    refresh['firstName'] = user.first_name
    return {
        'access': str(refresh.access_token),   # token scurt (5 min)
        'refresh': str(refresh),               # token lung (1 zi)
    }


@api_view(['POST'])
@permission_classes([AllowAny])   # acest endpoint nu cere autentificare
def signup(request):
    """
    POST /api/auth/signup
    Body: { firstName, lastName, email, password, role }

    Creeaza un user nou in PostgreSQL, returneaza token JWT + date user.
    Echivalentul endpoint-ului POST /api/auth/signup din Node.js.
    """
    data = request.data
    required = ['firstName', 'lastName', 'email', 'password', 'role']
    for field in required:
        if not data.get(field):
            return Response({'message': f'{field} is required'}, status=status.HTTP_400_BAD_REQUEST)

    if data['role'] not in ('student', 'teacher'):
        return Response({'message': 'role must be student or teacher'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=data['email']).exists():
        return Response({'message': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        email=data['email'],
        password=data['password'],         # hashing-ul e facut in create_user → set_password()
        role=data['role'],
        first_name=data['firstName'],
        last_name=data['lastName'],
    )

    tokens = tokens_for_user(user)
    return Response({
        'token': tokens['access'],
        'refresh': tokens['refresh'],
        'user': user_payload(user),
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    POST /api/auth/login
    Body: { email, password, role }

    Verifica credentialele, returneaza token JWT daca sunt corecte.
    Verifica si role-ul — un student nu poate loga ca teacher si invers.
    """
    email    = request.data.get('email', '').strip()
    password = request.data.get('password', '')
    role     = request.data.get('role', '')

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.check_password(password):        # compara parola cu hash-ul din DB
        return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    if user.role != role:
        return Response({'message': f'This account is not a {role} account'}, status=status.HTTP_401_UNAUTHORIZED)

    tokens = tokens_for_user(user)
    return Response({
        'token': tokens['access'],
        'refresh': tokens['refresh'],
        'user': user_payload(user),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """
    GET /api/auth/me
    Header: Authorization: Bearer <token>

    Valideaza token-ul JWT (simplejwt face asta automat prin middleware)
    si returneaza datele userului curent.
    Folosit de AuthContext la reincarcarea paginii — verifica daca token-ul
    din localStorage e inca valid.
    """
    return Response({'user': user_payload(request.user)})
