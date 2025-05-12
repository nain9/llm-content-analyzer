import firebase_admin
from firebase_admin import credentials, firestore
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entities.user import User


class FirebaseService:
    """Сервис для взаимодействия с Firebase Firestore."""

    def __init__(self, credentials_path: str):
        """Инициализация сервиса Firebase Firestore."""
        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def save_user(self, user: 'User') -> None:
        """Сохранить данные пользователя в Firestore."""
        self.db.collection('users').document(str(user.user_id)).set(user.to_dict())

    def get_user(self, user_id: int) -> 'User':
        """Получить пользователя из Firestore или создать нового, если не найден."""
        from entities.user import User
        doc_ref = self.db.collection('users').document(str(user_id))
        doc = doc_ref.get()
        user_data = doc.to_dict() if doc.exists else None
        if user_data:
            user = User.from_dict(user_data)
        else:
            user = User(user_id=user_id)
            self.save_user(user)
        return user

    def delete_user(self, user_id: int) -> None:
        """Удалить пользователя из Firestore."""
        self.db.collection('users').document(str(user_id)).delete()
