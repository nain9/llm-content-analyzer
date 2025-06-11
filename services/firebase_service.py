from google.oauth2 import service_account
from google.cloud.firestore_v1.async_client import AsyncClient

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entities.user import User


class FirebaseService:
    """Сервис для взаимодействия с Firebase Firestore."""

    def __init__(self, credentials_path: str):
        """Инициализация сервиса Firebase Firestore."""
        cred = service_account.Credentials.from_service_account_file(
            filename=credentials_path
        )
        self.db = AsyncClient(credentials=cred)

    async def save_user(self, user: 'User') -> None:
        """Сохранить пользователя в Firestore."""
        doc_ref = self.db.collection("users").document(
            document_id=str(user.user_id)
            )
        await doc_ref.set(user.to_dict())

    async def get_user(self, user_id: int) -> 'User':
        """Получить пользователя из Firestore или создать нового."""
        from entities.user import User

        doc_ref = self.db.collection("users").document(
            document_id=str(user_id)
            )
        doc = await doc_ref.get()
        user_data = doc.to_dict() if doc.exists else None

        if user_data:
            user = User.from_dict(user_data)
        else:
            user = User(user_id=user_id)
            await self.save_user(user)

        user.set_firebase_service(self)
        return user