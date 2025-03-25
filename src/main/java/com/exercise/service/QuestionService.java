package com.exercise.service;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.dao.EmptyResultDataAccessException;

import java.util.List;
import java.util.Map;

@Service
public class QuestionService {

    private final JdbcTemplate jdbcTemplate;

    public QuestionService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<String> getAllQuestionBanks() {
        String sql = "SELECT table_name FROM information_schema.tables " +
                "WHERE table_schema = DATABASE() AND table_name REGEXP '^[a-z0-9_]+$'";
        return jdbcTemplate.queryForList(sql, String.class);
    }

    public List<Map<String, Object>> getQuestions(String bankName) {
        validateTableName(bankName);

        String sql = "SELECT id, question, A, B, C, D, E, F, G, H, ans FROM " + bankName;
        return jdbcTemplate.queryForList(sql);
    }

    // 校验表名合法性
    private void validateTableName(String tableName) {
        if (!tableName.matches("^[a-z0-9_]{1,64}$")) {
            throw new SecurityException("Invalid table name");
        }

        try {
            jdbcTemplate.queryForObject(
                    "SELECT 1 FROM information_schema.tables " +
                            "WHERE table_schema = DATABASE() AND table_name = ?",
                    Integer.class,
                    tableName);
        } catch (EmptyResultDataAccessException e) {
            throw new IllegalArgumentException("题库不存在");
        }
    }
}