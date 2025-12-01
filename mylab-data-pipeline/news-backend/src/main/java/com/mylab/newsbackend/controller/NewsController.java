package com.mylab.newsbackend.controller;

import com.mylab.newsbackend.dto.NewsDto;
import com.mylab.newsbackend.service.NewsService;
import org.springframework.web.bind.annotation.*;
import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api/news")
@RequiredArgsConstructor
public class NewsController {

    private final NewsService newsService;

    // Airflow가 데이터를 보낼 곳 (POST 요청)
    @PostMapping
    public String saveNews(@RequestBody NewsDto newsDto) {
        newsService.saveNews(newsDto);
        return "✅ 뉴스 저장 완료: " + newsDto.getTitle();
    }
}
