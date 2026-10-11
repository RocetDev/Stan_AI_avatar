import base64
import textwrap
import argparse
import os
import sys


def convert_file_to_chunks(filepath: str, prefix: str, chunk_size: int = 80) -> str:
    """
    Читает файл, конвертирует в base64 и разбивает на короткие строки.
    Возвращает готовый JS-код для вставки в index.html.
    """
    if not os.path.exists(filepath):
        print(f"❌ Ошибка: Файл '{filepath}' не найден!")
        sys.exit(1)

    with open(filepath, 'rb') as f:
        raw_bytes = f.read()

    # Конвертация в base64
    raw_base64 = base64.b64encode(raw_bytes).decode('utf-8')

    # Разбиение на чанки (короткие строки по 80 символов)
    chunks = textwrap.wrap(raw_base64, chunk_size)

    # Формирование JS-массива
    var_name = "MODEL" if "model" in prefix else "MARKER"
    output = f"const {var_name}_BASE64_CHUNKS = [\n"
    output += f'    "{prefix}",\n'
    for chunk in chunks:
        output += f'    "{chunk}",\n'
    output += "];\n"

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Конвертирует .glb и .patt файлы в Base64 для вставки в HTML"
    )
    parser.add_argument(
        "--model", "-m",
        default="StanNew.glb",
        help="Путь к .glb файлу модели (по умолчанию: StanNew.glb)"
    )
    parser.add_argument(
        "--pattern", "-p",
        default="Stan_pattern.patt",
        help="Путь к .patt файлу маркера (по умолчанию: Stan_pattern.patt)"
    )
    parser.add_argument(
        "--output", "-o",
        default="base64_output.txt",
        help="Имя выходного файла (по умолчанию: base64_output.txt)"
    )
    parser.add_argument(
        "--chunk-size", "-c",
        type=int,
        default=80,
        help="Длина одной строки в чанке (по умолчанию: 80)"
    )

    args = parser.parse_args()

    print("🔄 Конвертация файлов в Base64...")

    # Префиксы Data URI
    MODEL_PREFIX = "data:model/gltf-binary;base64,"
    MARKER_PREFIX = "data:application/octet-stream;base64,"

    # Конвертация
    model_code = convert_file_to_chunks(args.model, MODEL_PREFIX, args.chunk_size)
    marker_code = convert_file_to_chunks(args.pattern, MARKER_PREFIX, args.chunk_size)

    # Запись результата
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write("// ============================================\n")
        f.write("// ⬇️ ВСТАВЬТЕ ЭТОТ БЛОК В index.html\n")
        f.write("// ============================================\n\n")
        f.write(model_code)
        f.write("\n")
        f.write(marker_code)
        f.write("\n// ============================================\n")

    size = os.path.getsize(args.output) / (1024 * 1024)
    print(f"✅ Готово! Результат сохранен в файл: '{args.output}' ({size:.2f} MB)")
    print(f"📋 Скопируйте содержимое файла и вставьте его в index.html,")
    print(f"   заменив блоки MODEL_BASE64_CHUNKS и MARKER_BASE64_CHUNKS.")


if __name__ == "__main__":
    main()