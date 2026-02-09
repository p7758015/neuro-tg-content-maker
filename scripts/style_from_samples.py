# scripts/style_from_samples.py
from app.examples.sample_posts import SAMPLE_POSTS
from app.services.style_extractor import extract_style
from app.services.style_store import save_style, load_style
from app.services.post_generator import generate_post


def main():
    style_name = input("Введи имя стиля (например, edler_channel): ").strip()

    existing = load_style(style_name)
    if existing:
        print("Стиль уже есть, используем сохранённый.\n")
        style = existing
    else:
        print("Стиля ещё нет, создаём из SAMPLE_POSTS...\n")
        style = extract_style(SAMPLE_POSTS)
        save_style(style_name, style)
        print("Стиль сохранён.\n")

    print("=== КРАТКИЙ СТИЛЬ АВТОРА ===")
    print(style["style_description"])

    post = generate_post(
        style=style,
        topic="Тестовый пост в стиле автора",
        goal="проверить, насколько похоже",
        audience="та же аудитория, что у канала",
    )

    print("\n=== СГЕНЕРИРОВАННЫЙ ПОСТ ===\n")
    print(post)


if __name__ == "__main__":
    main()
