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
import java.nio.file.*;
import java.util.ArrayList;
import java.util.List;

@Controller
public class FileUploadController {

    private static final String UPLOAD_DIR = "uploads";

    @GetMapping("/upload")
    public String uploadPage() {
        return "upload";
    }

    @PostMapping("/upload")
    public String handleUpload(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "password", required = false) String password,
            Model model) {

        try {
            String originalFilename = file.getOriginalFilename();
            if (originalFilename == null || originalFilename.isBlank()) {
                model.addAttribute("error", "未选择文件");
                return "upload";
            }

            String suffix = originalFilename.toLowerCase();
            if (!suffix.endsWith(".pdf") && !suffix.endsWith(".docx")) {
                model.addAttribute("error", "仅支持 PDF 或 Word (.docx) 文件");
                return "upload";
            }

            // 保存上传文件
            Path uploadPath = Paths.get(UPLOAD_DIR);
            if (!Files.exists(uploadPath))
                Files.createDirectories(uploadPath);
            Path filePath = uploadPath.resolve(originalFilename);
            file.transferTo(filePath);

            String output;
            if (suffix.endsWith(".pdf")) {
                Path finalPdf = filePath;

                if (password != null && !password.isBlank()) {
                    Path decryptedPath = uploadPath.resolve("decrypted_" + originalFilename);
                    String decryptOutput = callPythonScript("scripts/remove_pdf_password.py",
                            new String[] { filePath.toString(), decryptedPath.toString(), password });

                    if (!decryptOutput.contains("Success")) {
                        model.addAttribute("error", "PDF 解密失败：" + decryptOutput);
                        return "upload";
                    }
                    finalPdf = decryptedPath;
                }

                output = callPythonScript("scripts/pdf_parser.py", new String[] { finalPdf.toString() });
            } else {
                output = callPythonScript("scripts/word_parser.py", new String[] { filePath.toString() });
            }

            if (output.contains("成功")) {
                model.addAttribute("message", "上传成功：" + output);
            } else {
                model.addAttribute("error", "解析失败：" + output);
            }

            Files.deleteIfExists(filePath);
        } catch (Exception e) {
            model.addAttribute("error", "服务器错误：" + e.getMessage());
            e.printStackTrace();
        }

        return "upload";
    }

    private String callPythonScript(String scriptPath, String[] args) throws IOException, InterruptedException {
        List<String> command = new ArrayList<>();
        command.add("python");
        command.add(scriptPath);
        if (args != null) {
            for (String arg : args) {
                command.add(arg);
            }
        }

        ProcessBuilder processBuilder = new ProcessBuilder(command);
        processBuilder.redirectErrorStream(true);
        Process process = processBuilder.start();

        StringBuilder output = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append("\n");
            }
        }

        process.waitFor();
        return output.toString();
    }
}
