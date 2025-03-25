package com.exercise.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.List;

@Controller
public class HomeController {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @GetMapping("/")
    public String homePage(Model model) {
        // 查询数据库是否存在任何题库表
        String sql = "SHOW TABLES";
        List<String> tables = jdbcTemplate.queryForList(sql, String.class);

        // 检查是否有题库表（排除系统表）
        boolean hasQuestionBanks = tables.stream().anyMatch(name -> !name.startsWith("sys_"));

        // 传递查询结果到前端
        model.addAttribute("hasQuestionBanks", hasQuestionBanks);

        return "index"; // 渲染 index.html
    }
}
