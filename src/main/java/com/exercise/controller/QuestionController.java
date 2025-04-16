package com.exercise.controller;

import com.exercise.service.QuestionService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Controller
@RequestMapping("/questions")
public class QuestionController {

    private final QuestionService questionService;

    public QuestionController(QuestionService questionService) {
        this.questionService = questionService;
    }

    /**
     * 显示所有题库列表页面
     */
    @GetMapping
    public String listQuestionBanks(Model model) {
        List<String> banks = questionService.getAllQuestionBanks();
        model.addAttribute("banks", banks);
        return "bank_list";
    }

    /**
     * 显示指定题库的所有题目页面
     */
    @GetMapping("/{bankName}")
    public String showBankQuestions(@PathVariable String bankName, Model model) {
        return showQuestionsByType(bankName, model, false);
    }

    /**
     * 显示综合练习页面（合并所有题库）
     */
    @GetMapping("/combined")
    public String combinedPractice(Model model) {
        return showQuestionsByType("综合练习", model, true);
    }

    /**
     * 显示题目页面的通用处理方法
     */
    private String showQuestionsByType(String bankName, Model model, boolean combined) {
        try {
            List<Map<String, Object>> questions;

            if (combined) {
                List<String> banks = questionService.getAllQuestionBanks();
                questions = banks.stream()
                        .flatMap(bank -> questionService.getQuestions(bank).stream())
                        .toList();
            } else {
                questions = questionService.getQuestions(bankName);
            }

            model.addAttribute("questions", questions);
            model.addAttribute("bankName", bankName);
            model.addAttribute("banks", questionService.getAllQuestionBanks());
            return "exam";

        } catch (Exception e) {
            model.addAttribute("error", "加载题库失败: " + e.getMessage());
            return "error";
        }
    }
}
