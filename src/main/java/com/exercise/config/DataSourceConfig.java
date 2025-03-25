package com.exercise.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.jdbc.DataSourceBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

import javax.sql.DataSource;

@Configuration
public class DataSourceConfig {

    @Value("${spring.datasource.url}")
    private String defaultUrl;

    @Value("${spring.datasource.username}")
    private String username;

    @Value("${spring.datasource.password}")
    private String password;

    @Bean
    @Primary
    public DataSource dataSource() {
        // 初始连接到默认数据库（无数据库名称）
        return DataSourceBuilder.create()
                .url(defaultUrl)
                .username(username)
                .password(password)
                .driverClassName("org.mariadb.jdbc.Driver")
                .build();
    }

    @Bean(name = "questionBankDataSource")
    public DataSource questionBankDataSource() {
        // 切换到 question_bank 数据库
        return DataSourceBuilder.create()
                .url("jdbc:mariadb://localhost:3306/question_bank?useSSL=false&serverTimezone=Asia/Shanghai")
                .username(username)
                .password(password)
                .driverClassName("org.mariadb.jdbc.Driver")
                .build();
    }
}