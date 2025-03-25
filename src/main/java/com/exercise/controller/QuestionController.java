package com.exercise.controller;

import com.exercise.service.QuestionService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;

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
     * 显示所有题库列表
     */
    @GetMapping
    public String listQuestionBanks(Model model) {
        try {
            List<String> banks = questionService.getAllQuestionBanks();
            model.addAttribute("banks", banks);
            return "bank_list";
        } catch (Exception e) {
            model.addAttribute("error", "题库加载失败: " + e.getMessage());
            return "error";
        }
    }

    /**
     * 显示指定题库的所有题目（支持页面内锚点定位）
     */
    @GetMapping("/{bankName}")
    public String showBankQuestions(
            @PathVariable String bankName,
            Model model) {
        try {
            // 获取题库的所有题目
            List<Map<String, Object>> questions = questionService.getQuestions(bankName);

            model.addAttribute("questions", questions);
            model.addAttribute("bankName", bankName);
            model.addAttribute("banks", questionService.getAllQuestionBanks());
            return "exam";
        } catch (Exception e) {
            model.addAttribute("error", "题库加载失败: " + e.getMessage());
            return "error";
        }
    }

    /**
     * 综合练习模式（合并所有题库）
     */
    @GetMapping("/combined")
    public String combinedPractice(Model model) {
        try {
            // 获取所有题库的题目
            List<String> banks = questionService.getAllQuestionBanks();
            List<Map<String, Object>> allQuestions = banks.stream()
                    .flatMap(bank -> questionService.getQuestions(bank).stream())
                    .toList();

            model.addAttribute("questions", allQuestions);
            model.addAttribute("bankName", "综合练习");
            model.addAttribute("banks", questionService.getAllQuestionBanks());
            return "exam";
        } catch (Exception e) {
            model.addAttribute("error", "综合题库加载失败: " + e.getMessage());
            return "error";
        }
    }
}