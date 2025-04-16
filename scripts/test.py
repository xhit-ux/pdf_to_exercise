import argparse
import pdfplumber
import re
import os
import io
import unicodedata
import pymysql


def sanitize_table_name(name):
    """规范化表名"""
    cleaned = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-zA-Z0-9_]', '_', cleaned)[:64].lower()


def extract_text_and_images(pdf_path, password=None):
    """提取 PDF 文本和图片"""
    text_lines = []
    images = []

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"文件不存在: {pdf_path}")

    try:
        with pdfplumber.open(pdf_path, password=password) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # --------- 提取文本 ---------
                text = page.extract_text()
                if text:
                    lines = text.split("\n")
                    for line in lines:
                        # 去除页码类行 - 1 - 或 -1-
                        if re.fullmatch(r'-\s*\d+\s*-', line.strip()):
                            continue
                        text_lines.append(line.strip())

                # --------- 提取图片 ---------
                for img_index, img_obj in enumerate(page.images):
                    # 获取图片数据
                    try:
                        img_data = page.extract_image(img_obj['object_id'])
                        if img_data and 'image' in img_data:
                            images.append({
                                "page_num": page_num,
                                "data": img_data['image']
                            })
                    except Exception:
                        continue

    except Exception as e:
        if "password" in str(e).lower():
            raise ValueError("PDF 需要密码，但提供的密码不正确或未提供密码")
        raise RuntimeError(f"无法解析 PDF 文件: {str(e)}")

    if not text_lines:
        raise ValueError("PDF 内容为空或未提取到有效文本")

    return text_lines, images


def parse_questions(text_lines):
    """解析题目、选项、答案"""
    title = text_lines[0]
    table_name = sanitize_table_name(title)

    questions = []
    current_q = None
    question_positions = []

    question_pattern = re.compile(r'^(\d+)[．\.]?\s*(.+)$')   # 支持 1. 或 1．
    option_pattern = re.compile(r'^([A-H])[．\.]?\s*(.*)$')   # 支持 A. 或 A．
    answer_pattern = re.compile(r'(?:正确答案|答案)[:：]([A-H]+)')   # 支持“正确答案：A”或“答案：A”

    for idx, line in enumerate(text_lines[1:]):
        if answer_match := answer_pattern.search(line):
            if current_q:
                current_q['ans'] = answer_match.group(1)
                questions.append(current_q)
                current_q = None
            continue

        if question_match := question_pattern.match(line):
            if current_q:
                questions.append(current_q)
            current_q = {
                'question': question_match.group(2).strip(),
                'A': '', 'B': '', 'C': '', 'D': '',
                'E': '', 'F': '', 'G': '', 'H': '',
                'ans': None, 'images': [],
                'line_idx': idx
            }
            question_positions.append(current_q)
            continue

        if option_match := option_pattern.match(line):
            if current_q:
                current_q[option_match.group(1)] = option_match.group(2).strip()
            continue

        if current_q:
            current_q['question'] += " " + line.strip()

    if current_q and current_q.get('ans'):
        questions.append(current_q)

    if not questions:
        raise ValueError("未解析出任何题目，请检查 PDF 格式")

    return table_name, questions


def match_images_to_questions(images, questions):
    """通过页码匹配图片到题目"""
    for img in images:
        page_num = img["page_num"]
        # 简单策略：图片分配给第一个在该页之后出现的题目
        for q in questions:
            if len(q['images']) >= 3:
                continue
            if q.get('page_num', 0) >= page_num:
                q['images'].append(img["data"])
                break


def connect_db():
    """数据库连接"""
    try:
        return pymysql.connect(
            host='127.0.0.1',
            user='exercise',
            password='12345678',
            db='question_bank',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    except pymysql.MySQLError as e:
        raise RuntimeError(f"数据库连接失败: {str(e)}")


def create_table(conn, table_name):
    """创建题库表"""
    with conn.cursor() as cursor:
        sql = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                question TEXT,
                A VARCHAR(512),
                B VARCHAR(512),
                C VARCHAR(512),
                D VARCHAR(512),
                E VARCHAR(512),
                F VARCHAR(512),
                G VARCHAR(512),
                H VARCHAR(512),
                image1 LONGBLOB,
                image2 LONGBLOB,
                image3 LONGBLOB,
                ans VARCHAR(10)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        cursor.execute(sql)
    conn.commit()


def save_questions_to_db(table_name, questions):
    """存入数据库"""
    conn = connect_db()
    try:
        create_table(conn, table_name)
        with conn.cursor() as cursor:
            sql = f"""
                INSERT INTO `{table_name}` 
                (question, A, B, C, D, E, F, G, H, image1, image2, image3, ans)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            data = [
                (
                    q['question'], q['A'], q['B'], q['C'], q['D'],
                    q['E'], q['F'], q['G'], q['H'],
                    q['images'][0] if len(q['images']) > 0 else None,
                    q['images'][1] if len(q['images']) > 1 else None,
                    q['images'][2] if len(q['images']) > 2 else None,
                    q['ans']
                )
                for q in questions
            ]
            cursor.executemany(sql, data)
        conn.commit()
        print(f"✅ 已成功创建表 `{table_name}`，共导入 {len(questions)} 道题")
    except pymysql.MySQLError as e:
        raise RuntimeError(f"数据库操作失败: {str(e)}")
    finally:
        conn.close()


def main(pdf_path, password=None):
    """主流程"""
    print("⏳ 开始解析 PDF ...")
    text_lines, images = extract_text_and_images(pdf_path, password)
    print("✅ 文本和图片提取完成")

    table_name, questions = parse_questions(text_lines)
    print(f"✅ 共解析出 {len(questions)} 道题目，表名：{table_name}")

    match_images_to_questions(images, questions)
    print(f"✅ 图片关联完成（共 {len(images)} 张图片）")

    save_questions_to_db(table_name, questions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="解析 PDF 题库并保存到数据库")
    parser.add_argument("pdf_path", help="PDF 文件路径")
    parser.add_argument("--password", help="PDF 密码（如有）", default=None)
    args = parser.parse_args()

    try:
        main(args.pdf_path, args.password)
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        exit(1)
