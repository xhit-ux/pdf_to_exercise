import argparse
import PyPDF2
import os
import sys
import tempfile
import shutil

def remove_pdf_password(input_pdf, pdf_password):
    """
    解锁 PDF 并直接覆盖原文件
    """
    try:
        # 读取 PDF
        with open(input_pdf, "rb") as f:
            reader = PyPDF2.PdfReader(f)

            if reader.is_encrypted:
                if not reader.decrypt(pdf_password):
                    print(f"❌ 解密失败，请检查密码是否正确：{input_pdf}")
                    return
                print(f"✅ 成功解密：{input_pdf}")
            else:
                print(f"⚠️ PDF 未加密：{input_pdf}")


            # 写入解密后的 PDF 到临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                writer = PyPDF2.PdfWriter()
                for page in reader.pages:
                    writer.add_page(page)
                writer.write(tmp_file)

            # 替换原文件（更安全）
            shutil.move(tmp_file.name, input_pdf)

            print(f"🎉 PDF 已成功解密并替换：{input_pdf}")

    except FileNotFoundError:
        print(f"❌ 文件不存在: {input_pdf}")
    except PyPDF2.errors.PdfReadError:
        print("❌ 该文件不是有效的 PDF，或者已损坏。")
    except Exception as e:
        print(f"⚠️ 处理过程中发生异常：{str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="去除 PDF 密码并覆盖原文件")
    parser.add_argument("pdf_path", help="PDF 文件路径")
    parser.add_argument("--password", help="PDF 文件的密码", required=True)
    args = parser.parse_args()

    if not os.path.isfile(args.pdf_path):
        print(f"❌ 文件不存在: {args.pdf_path}")
        sys.exit(1)

    remove_pdf_password(args.pdf_path, args.password)
