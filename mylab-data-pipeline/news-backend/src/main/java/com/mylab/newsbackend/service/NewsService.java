package com.mylab.newsbackend.service;

import com.mylab.newsbackend.dto.NewsDto;

public interface NewsService {
    void saveNews(NewsDto newsDto);
}