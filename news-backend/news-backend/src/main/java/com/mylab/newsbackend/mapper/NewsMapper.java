package com.mylab.newsbackend.mapper;

import com.mylab.newsbackend.dto.NewsDto;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface NewsMapper {
    // 뉴스 저장하기 (Insert)
    void saveNews(NewsDto newsDto);
}
