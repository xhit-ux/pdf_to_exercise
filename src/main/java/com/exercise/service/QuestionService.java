package com.exercise.service;

import org.springframework.dao.EmptyResultDataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.sql.Blob;
import java.util.ArrayList;
import java.util.HashMap;
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

        String sql = "SELECT id, question, A, B, C, D, E, F, G, H, ans, image1, image2, image3 FROM " + bankName;
        return jdbcTemplate.query(sql, rs -> {
            List<Map<String, Object>> questions = new ArrayList<>();
            while (rs.next()) {
                Map<String, Object> q = new HashMap<>();
                q.put("id", rs.getInt("id"));
                q.put("question", rs.getString("question"));
                q.put("A", rs.getString("A"));
                q.put("B", rs.getString("B"));
                q.put("C", rs.getString("C"));
                q.put("D", rs.getString("D"));
                q.put("E", rs.getString("E"));
                q.put("F", rs.getString("F"));
                q.put("G", rs.getString("G"));
                q.put("H", rs.getString("H"));
                q.put("ans", rs.getString("ans"));

                // 处理图片字段，转换为 byte[]
                q.put("image1", getBytesFromBlob(rs.getBlob("image1")));
                q.put("image2", getBytesFromBlob(rs.getBlob("image2")));
                q.put("image3", getBytesFromBlob(rs.getBlob("image3")));

                questions.add(q);
            }
            return questions;
        });
    }

    private byte[] getBytesFromBlob(Blob blob) {
        try {
            if (blob != null) {
                return blob.getBytes(1, (int) blob.length());
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
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
