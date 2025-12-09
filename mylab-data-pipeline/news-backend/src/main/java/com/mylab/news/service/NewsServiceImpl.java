package com.mylab.news.service;

import com.mylab.news.dto.NewsDto;
import com.mylab.news.mapper.NewsMapper;
import org.springframework.stereotype.Service;
import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class NewsServiceImpl implements NewsService {

    private final NewsMapper newsMapper; // 매퍼(DAO) 소환

    @Override
    public void saveNews(NewsDto newsDto) {
        // 나중에 여기서 데이터 가공이나 검증 로직을 넣을 수 있음
        System.out.println("💾 DB 저장 요청: " + newsDto.getTitle());
        newsMapper.saveNews(newsDto);
    }
}