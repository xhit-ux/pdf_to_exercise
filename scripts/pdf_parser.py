import pdfplumber
import re
import sys
import os
import unicodedata
import pymysql
import argparse

def sanitize_table_name(name):
    """ 规范化表名，去除特殊字符，并限制长度 """
    cleaned = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-zA-Z0-9_]', '_', cleaned)[:64].lower()

def remove_page_numbers(content):
    """ 过滤页码，例如 -1-、-2- 等 """
    # 匹配页码格式：-数字-
    page_number_pattern = re.compile(r'- \d+ -')
    return page_number_pattern.sub('', content)

def parse_pdf(pdf_path, password=None):
    """ 解析 PDF 题库，返回表名、标题和解析后的问题列表 """
    
    # 读取 PDF 文本
    try:
        with pdfplumber.open(pdf_path, password=password) as pdf:
            content = '\n'.join(filter(None, (page.extract_text() for page in pdf.pages)))
    except Exception as e:
        # 判断是否是密码错误
        if "password" in str(e).lower():
            return None, None, None, "PDF 文件需要密码，但提供的密码不正确或未提供密码。"
        return None, None, None, f"无法解析 PDF 文件：{str(e)}"
    
    # 过滤页码
    content = remove_page_numbers(content)
    
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    # 解析标题
    if not lines:
        return None, None, None, "PDF 内容为空，无法解析"
    
    title = lines[0]
    table_name = sanitize_table_name(title)
    
    # 解析题目
    questions = []
    current_q = None
    current_option = None
    
    question_pattern = re.compile(r'^(\d+)．\s*(.+)$')  # 题目编号匹配
    option_pattern = re.compile(r'^([A-H])[．.]?\s*(.*)$')  # 选项匹配（支持 A. 和 A．）
    answer_pattern = re.compile(r'正确答案：([A-H]+)')  # 多选支持，例如 "正确答案：AC"
    
    for line in lines[1:]:
        # 匹配答案
        if answer_match := answer_pattern.match(line):
            if current_q:
                current_q['ans'] = answer_match.group(1)
                questions.append(current_q)
                current_q = None
                current_option = None  # 重置选项
            continue
        
        # 匹配题目编号
        if question_match := question_pattern.match(line):
            if current_q:
                questions.append(current_q)
            current_q = {'question': question_match.group(2).strip(), 'A': '', 'B': '', 'C': '', 'D': '', 'E': '','F': '','G': '','H': '','ans': None}
            current_option = None  # 新题目开始时重置选项
            continue
        
        # 匹配选项
        if option_match := option_pattern.match(line):
            option_key = option_match.group(1)  # A, B, C, D
            if current_q:
                current_q[option_key] = option_match.group(2).strip()
                current_option = option_key
            continue
        
        # **题干换行合并**
        if current_q and current_option is None:
            # 当前行不是新题目、不是选项，也不是答案 => 题目换行
            current_q["question"] += " " + line.strip()
            continue
        
        # **选项换行合并**
        if current_q and current_option:
            current_q[current_option] += " " + line.strip()
    
    # 处理最后一个题目
    if current_q and current_q['ans'] is not None:
        questions.append(current_q)

    # 返回解析结果
    return table_name, title, questions, None


def save_to_db(table_name, questions):
    try:
        conn = pymysql.connect(
            host='127.0.0.1',
            user='exercise',
            password='12345678',
            db='question_bank',  # 指定数据库
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # 创建表（如果不存在）
            cursor.execute(f"""
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
                    ans VARCHAR(10)  -- 多选题支持
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # 批量插入数据
            sql = f"""
                INSERT INTO `{table_name}` 
                (question, A, B, C, D, E, F, G, H, ans)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            batch_data = [
                (q['question'], q['A'], q['B'], q['C'], q['D'], q['E'], q['F'], q['G'], q['H'], q['ans'])
                for q in questions
            ]
            
            cursor.executemany(sql, batch_data)
        conn.commit()
    except Exception as e:
        print(f"Database error: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # 使用 argparse 解析命令行参数
    parser = argparse.ArgumentParser(description="解析 PDF 题库并保存到数据库")
    parser.add_argument("pdf_path", help="PDF 文件路径")
    parser.add_argument("--password", help="PDF 文件的密码（可选）", default=None)
    args = parser.parse_args()

    pdf_path = args.pdf_path
    password = args.password

    if not os.path.isfile(pdf_path):
        print(f"文件不存在: {pdf_path}")
        sys.exit(1)
    
    try:
        table_name, title, questions, error = parse_pdf(pdf_path, password)
        if error:
            print(error)
            sys.exit(1)
        
        save_to_db(table_name, questions)
        print(f"成功：创建表 '{table_name}'，并插入 {len(questions)} 条题目")
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")
        sys.exit(1)