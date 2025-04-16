import argparse
import sys
import unicodedata
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from io import BytesIO
import base64
import re
import os

import pymysql


def sanitize_table_name(name):
    """ 规范化表名，去除特殊字符，并限制长度 """
    cleaned = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-zA-Z0-9_]', '_', cleaned)[:64].lower()

def parse_word(word_path):
    try:
        doc = Document(word_path)
    except Exception as e:
        return None, None, None, f"无法打开 Word 文件：{str(e)}"

    paragraphs = doc.paragraphs
    title = os.path.splitext(os.path.basename(word_path))[0]
    table_name = sanitize_table_name(title)

    questions = []
    current_q = None
    current_option = None
    current_images = []

    # 提取图片映射（rId -> image binary）
    image_map = {}
    rels = doc.part.rels
    for rel in rels.values():
        if rel.reltype == RT.IMAGE:
            image_map[rel.rId] = rel.target_part.blob

    # 处理每段文字（或图片）
    question_pattern = re.compile(r'^(\d+)[. ．、]?\s*(.+)')
    option_pattern = re.compile(r'^([A-H])[.．、]?\s*(.+)')
    answer_pattern = re.compile(r'答案[:：]?\s*([A-H]+)', re.IGNORECASE)

    for para in paragraphs:
        text = para.text.strip()

        # 图片（紧跟题干或选项后）
        for run in para.runs:
            if 'drawing' in run._element.xml:
                # 查找图片 rId
                blip = run._element.xpath(".//a:blip")
                if blip:
                    rId = blip[0].get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
                    if rId in image_map:
                        current_images.append(image_map[rId])

        # 空行跳过
        if not text:
            continue

        # 匹配答案
        if answer_match := answer_pattern.match(text):
            if current_q:
                current_q["ans"] = answer_match.group(1)
                current_q["images"] = current_images[:3]
                questions.append(current_q)
                current_q = None
                current_option = None
                current_images = []
            continue

        # 匹配题目
        if question_match := question_pattern.match(text):
            if current_q:
                current_q["images"] = current_images[:3]
                questions.append(current_q)
                current_images = []
            current_q = {
                "question": question_match.group(2),
                "A": "", "B": "", "C": "", "D": "",
                "E": "", "F": "", "G": "", "H": "",
                "ans": None,
                "images": []
            }
            current_option = None
            continue

        # 匹配选项
        if option_match := option_pattern.match(text):
            if current_q:
                current_q[option_match.group(1)] = option_match.group(2)
                current_option = option_match.group(1)
            continue

        # 题干续行
        if current_q and current_option is None:
            current_q["question"] += " " + text
            continue

        # 选项续行
        if current_q and current_option:
            current_q[current_option] += " " + text

    # 处理最后一题
    if current_q and current_q["ans"]:
        current_q["images"] = current_images[:3]
        questions.append(current_q)

    return table_name, title, questions, None


def save_to_db(table_name, questions):
    try:
        conn = pymysql.connect(
            host='127.0.0.1',
            user='exercise',
            password='12345678',
            db='question_bank',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS `{table_name}` (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    question TEXT,
                    A VARCHAR(512), B VARCHAR(512), C VARCHAR(512), D VARCHAR(512),
                    E VARCHAR(512), F VARCHAR(512), G VARCHAR(512), H VARCHAR(512),
                    image1 LONGBLOB, image2 LONGBLOB, image3 LONGBLOB,
                    ans VARCHAR(10)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            sql = f"""
                INSERT INTO `{table_name}` 
                (question, A, B, C, D, E, F, G, H, image1, image2, image3, ans)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            for q in questions:
                if len(q["D"]) > 512:
                    print("超长选项：", q["D"])
                image_data = q.get('images', [])  # 默认 []
                image1 = image_data[0] if len(image_data) > 0 else None
                image2 = image_data[1] if len(image_data) > 1 else None
                image3 = image_data[2] if len(image_data) > 2 else None

                cursor.execute(sql, (
                    q['question'], q['A'], q['B'], q['C'], q['D'],
                    q['E'], q['F'], q['G'], q['H'],
                    image1, image2, image3,
                    q['ans']
                ))

        conn.commit()
    except Exception as e:
        print(f"Database error: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="解析 Word 题库文件并写入数据库")
    parser.add_argument("word_path", help="Word (.docx) 文件路径")
    args = parser.parse_args()

    word_path = args.word_path

    if not os.path.isfile(word_path):
        print(f"文件不存在: {word_path}")
        sys.exit(1)

    try:
        table_name, title, questions, error = parse_word(word_path)
        if error:
            print(error)
            sys.exit(1)

        save_to_db(table_name, questions)
        print(f"成功：创建表 '{table_name}'，并插入 {len(questions)} 条题目")
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")
        sys.exit(1)
