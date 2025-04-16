import time
import pdfplumber
import re
import sys
import os
import unicodedata
import pymysql
import argparse

def sanitize_table_name(name):
    """规范化表名，去除特殊字符，并限制长度，确保不为空"""
    cleaned = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', cleaned)[:64].lower()
    return cleaned or f"table_{int(time.time())}"


def remove_page_numbers(content):
    return re.sub(r'- ?\d+ -', '', content)

def parse_pdf(pdf_path, password=None):
    try:
        with pdfplumber.open(pdf_path, password=password) as pdf:
            content = '\n'.join(filter(None, (page.extract_text() for page in pdf.pages)))
    except Exception as e:
        if "password" in str(e).lower():
            return None, None, None, "PDF 文件需要密码，但提供的密码不正确或未提供密码。"
        return None, None, None, f"无法解析 PDF 文件：{str(e)}"

    content = remove_page_numbers(content)
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    if not lines:
        return None, None, None, "PDF 内容为空，无法解析"

    title = lines[0]
    table_name = sanitize_table_name(title)

    questions = []
    current_q = None
    current_option = None

    # 题目行：1、xxx (B)
    question_pattern = re.compile(r'^(\d+)[、．. ]+(.+)$')
    embedded_answer_pattern = re.compile(r'^(.*?)[。？?.（(] ?([A-H]) ?[)）]\s*$')
    option_pattern = re.compile(r'^([A-H])[．.、]?\s*(.+)$')
    explicit_answer_pattern = re.compile(r'正确答案[:：]?\s*([A-H]+)', re.IGNORECASE)

    for line in lines[1:]:
        # 显式答案行
        if explicit_answer_pattern.match(line):
            answer = explicit_answer_pattern.match(line).group(1).strip()
            if current_q:
                current_q['ans'] = answer
                questions.append(current_q)
                current_q = None
                current_option = None
            continue

        # 新题目行（题干可能内嵌答案）
        if question_pattern.match(line):
            if current_q:
                questions.append(current_q)
            num, body = question_pattern.match(line).groups()
            body = body.strip()

            embedded_match = embedded_answer_pattern.match(body)
            if embedded_match:
                question_text = embedded_match.group(1).strip()
                answer = embedded_match.group(2).strip()
            else:
                question_text = body
                answer = None

            current_q = {
                'question': question_text,
                'A': '', 'B': '', 'C': '', 'D': '',
                'E': '', 'F': '', 'G': '', 'H': '',
                'ans': answer,
                'images': []
            }
            current_option = None
            continue

        # 选项行
        if option_pattern.match(line):
            if current_q:
                key, value = option_pattern.match(line).groups()
                current_q[key] = value.strip()
                current_option = key
            continue

        # 题干续行
        if current_q and current_option is None:
            current_q['question'] += " " + line.strip()
            continue

        # 选项续行
        if current_q and current_option:
            current_q[current_option] += " " + line.strip()

    # 最后一题
    if current_q and current_q.get('ans'):
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
                    A VARCHAR(1024), B VARCHAR(1024), C VARCHAR(1024), D VARCHAR(1024),
                    E VARCHAR(1024), F VARCHAR(1024), G VARCHAR(1024), H VARCHAR(1024),
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
                image_data = q.get('images', [])
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
    parser = argparse.ArgumentParser(description="解析 PDF 题库并保存到数据库")
    parser.add_argument("pdf_path", help="PDF 文件路径")
    parser.add_argument("--password", help="PDF 文件的密码（可选）", default=None)
    args = parser.parse_args()

    if not os.path.isfile(args.pdf_path):
        print(f"文件不存在: {args.pdf_path}")
        sys.exit(1)

    try:
        table_name, title, questions, error = parse_pdf(args.pdf_path, args.password)
        if error:
            print(error)
            sys.exit(1)

        save_to_db(table_name, questions)
        print(f"成功：创建表 '{table_name}'，并插入 {len(questions)} 条题目")
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")
        sys.exit(1)
