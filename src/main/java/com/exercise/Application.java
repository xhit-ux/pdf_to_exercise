package com.exercise;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.jdbc.core.JdbcTemplate;

@SpringBootApplication
public class Application {

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }

    @Bean
    public String initializeDatabase(JdbcTemplate jdbcTemplate) {
        try {
            // 检查数据库连接是否正常
            jdbcTemplate.execute("SELECT 1");
            System.out.println("数据库连接成功，初始化完成！");
        } catch (Exception e) {
            System.err.println("数据库连接失败，请检查配置！");
            e.printStackTrace();
        }
        return "Database initialized";
    }
}