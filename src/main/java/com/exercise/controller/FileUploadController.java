package com.exercise.controller;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.multipart.MultipartFile;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

@Controller
public class FileUploadController {

    // 定义上传文件存储目录
    private static final String UPLOAD_DIR = "uploads";

    @GetMapping("/upload")
    public String uploadPage() {
        return "upload"; // 返回 upload.html 页面
    }

    @SuppressWarnings("null")
    @PostMapping("/upload")
    public String handleUpload(
            @RequestParam("file") MultipartFile file,
            Model model) {
        try {
            // 校验文件类型
            if (!file.getContentType().equals("application/pdf")) {
                model.addAttribute("error", "仅支持 PDF 文件");
                return "upload";
            }

            // 创建上传目录（如果不存在）
            Path uploadPath = Paths.get(UPLOAD_DIR);
            if (!Files.exists(uploadPath)) {
                Files.createDirectories(uploadPath);
            }

            // 保存文件到 /uploads 目录
            Path filePath = uploadPath.resolve(file.getOriginalFilename());
            file.transferTo(filePath);

            // 调用 Python 脚本
            String output = callPythonScript(filePath.toString(), null);

            // 检查解析结果
            if (output.contains("成功")) {
                model.addAttribute("message", "上传成功：" + output);
            } else {
                model.addAttribute("error", "解析失败：" + output);
            }

            // 删除上传的文件
            Files.deleteIfExists(filePath);
        } catch (Exception e) {
            model.addAttribute("error", "服务器错误：" + e.getMessage());
        }
        return "upload"; // 返回 upload.html 页面
    }

    private String callPythonScript(String filePath, String password) throws IOException, InterruptedException {
        // 构建 Python 脚本命令
        String pythonScriptPath = "scripts/pdf_parser.py";
        ProcessBuilder processBuilder = new ProcessBuilder("python", pythonScriptPath, filePath);

        // 如果有密码，添加 --password 参数
        if (password != null) {
            processBuilder.command().add("--password");
            processBuilder.command().add(password);
        }

        // 启动进程
        Process process = processBuilder.redirectErrorStream(true).start();

        // 获取执行结果
        StringBuilder output = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append("\n");
            }
        }

        // 等待进程结束
        process.waitFor();
        return output.toString();
    }
}