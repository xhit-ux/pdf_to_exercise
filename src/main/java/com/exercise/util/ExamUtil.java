package com.exercise.util;

import java.util.LinkedHashMap;
import java.util.Map;

public class ExamUtil {

    // 将问题对象转换为选项Map
    public static Map<String, String> getOptions(Map<String, Object> question) {
        Map<String, String> options = new LinkedHashMap<>();

        // 动态添加选项，从 A 到 H
        for (char option = 'A'; option <= 'H'; option++) {
            String key = String.valueOf(option);
            String value = (String) question.get(key);
            addOption(options, key, value);
        }

        return options;
    }

    // 安全添加选项（过滤空值）
    private static void addOption(Map<String, String> map, String key, String value) {
        if (value != null && !value.trim().isEmpty()) {
            map.put(key, value);
        }
    }

    // 验证答案格式
    public static boolean isValidAnswer(String ans) {
        return ans != null && ans.matches("^[A-H]$"); // 支持 A 到 H
    }
}