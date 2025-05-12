from dataclasses import dataclass


@dataclass
class AnalysisData:
    """Класс для хранения данных анализа поста."""

    platform: str = ""
    blog_type: str = ""
    purpose: str = ""
    audience: str = ""
    post_text: str = ""

    def to_dict(self) -> dict:
        """Преобразовать объект анализа в словарь для сохранения."""
        return {
            'platform': self.platform,
            'blog_type': self.blog_type,
            'purpose': self.purpose,
            'audience': self.audience,
            'post_text': self.post_text,
        }

    @staticmethod
    def from_dict(data: dict) -> 'AnalysisData':
        """Создать объект анализа из словаря."""
        return AnalysisData(**data)
