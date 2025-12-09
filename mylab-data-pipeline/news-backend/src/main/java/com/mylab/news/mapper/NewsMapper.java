package com.mylab.news.mapper;

import com.mylab.news.dto.NewsDto;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface NewsMapper {
    // 뉴스 저장하기 (Insert)
    void saveNews(NewsDto newsDto);
}
