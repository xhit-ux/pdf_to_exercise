 # pdf_to_exercise

## 概述
pdf_to_exercise 是一个基于 Python 与 Spring Boot 的在线练习平台，通过解析 PDF 和 Word 格式的题库文件，将题目、选项、答案及图片存储到 MariaDB 数据库，并提供网页端上传、练习、综合练习功能 

## 功能
- 支持 PDF 题库文件解析，包括带密码的 PDF 解密与解析   
- 支持 Word (.docx) 题库文件解析，包括题干图片提取与存储 
- 将解析结果（题目、选项、答案、图片）存入 MariaDB 的 `question_bank` 数据库 
- 提供上传页面，通过前端上传文件并调用 Python 脚本进行解析 
- 提供题库列表、题库练习和综合练习页面，实时展示题目并支持答题 
- 基于 Thymeleaf 模板引擎构建前端页面，支持静态资源和模板自定义 

## 架构
- 后端使用 Spring Boot 框架，Java 17 开发，提供页面渲染与业务逻辑支持 
- 数据库使用 MariaDB，通过 Spring JDBC 与 `JdbcTemplate` 访问数据 
- Python 脚本负责解析 PDF 与 Word 文件，依赖 `pdfplumber`、`PyPDF2`、`python-docx` 与 `pymysql` 等库 
- 前端使用 Thymeleaf 渲染 HTML 页面，静态资源统一放置在 `/static` 目录 

## 安装与运行

### 前提条件
- Java 17 环境与 Maven 构建工具 
- Python 3 环境与 pip 包管理器 
- MariaDB 数据库实例，并创建数据库 `question_bank` 

### 配置数据库
1. 克隆仓库并进入项目根目录。  
2. 编辑 `src/main/resources/application.yaml`，修改 `spring.datasource` 配置为你的数据库地址、用户名、密码 
3. （可选）执行 `src/main/resources/schema.sql` 初始化所需的表结构 

### 安装 Python 依赖
```bash
pip install -r requirements.txt
``` 

### 构建并运行 Java 应用
```bash
mvn clean package
java -jar target/pdf_to_exercise.jar
``` 

## 使用说明
1. 访问 `http://localhost:8080/` 查看首页，判断是否已有题库可练习  
2. 通过导航栏进入 “题库上传” 页面，选择 PDF 或 DOCX 文件上传，支持输入 PDF 密码  
3. 上传成功后，通过 “题库列表” 或 “综合练习” 页面进行在线答题 

## 项目结构
```bash
pdf_to_exercise 
 ├── scripts 
 │ ├── remove_pdf_password.py # PDF 解密脚本 
 │ ├── pdf_parser.py # PDF 解析脚本 
 │ └── word_parser.py # Word 文档解析脚本 
 ├── uploads #用于暂时存放上传的文件
 ├── src 
 │ ├── main 
 │ │ ├── java 
 │ │ │ └── com 
 │ │ │   └── exercise
 │ │ │     ├── config # 数据源与 Web 资源配置 
 │ │ │     │ ├── WebConfig.java
 │ │ │     │ └── DataSourceConfig.java
 │ │ │     ├── controller # 上传与题库控制器 
 │ │ │     │ ├── FileUploadController.java
 │ │ │     │ ├── HomeController.java
 │ │ │     │ └── QuestionController.java
 │ │ │     ├── service # 题库业务逻辑 
 │ │ │     │ └── QuestionService.java
 │ │ │     ├── util # 前端渲染辅助工具
 │ │ │     │ └── ExamUtil.java
 │ │ │     └── Application.java
 │ │ └── resources 
 │ │   ├── static # 静态资源 
 │ │   ├── templates # Thymeleaf 模板 
 │ │   ├── application.yaml # 应用配置 
 │ │   └── schema.sql # 数据库初始化脚本 
 │ └── test # 单元测试（可拓展） 
 ├── requirements.txt # Python 依赖 
 └── pom.xml # Maven 构建配置