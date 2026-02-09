# scripts/demo_generate_post.py
from app.examples.sample_posts import SAMPLE_POSTS
from app.services.style_extractor import extract_style
from app.services.post_generator import generate_post

def main():
    style = extract_style(SAMPLE_POSTS)
    print("=== СТИЛЬ АВТОРА (кратко) ===")
    print(style["style_description"])
    print("\n=== ХАРАКТЕРНЫЕ ФРАЗЫ ===")
    print(", ".join(style["preferred_phrases"][:10]))

    post = generate_post(
        style=style,
        topic="Запуск мини-урока по AutoML",
        goal="мягко прогреть аудиторию к регистрации",
        audience="новички в Data Science, которые боятся сложной математики",
    )

    print("\n=== СГЕНЕРИРОВАННЫЙ ПОСТ ===\n")
    print(post)

if __name__ == "__main__":
    main()
