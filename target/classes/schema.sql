-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS question_bank
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 切换到 question_bank 数据库
USE question_bank;

-- 创建题库表模板（动态表名由 Python 脚本创建）
-- 这里只需要确保数据库存在即可