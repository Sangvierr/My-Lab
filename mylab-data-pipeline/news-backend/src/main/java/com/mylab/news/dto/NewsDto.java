package com.mylab.news.dto;

import lombok.Data;
import java.util.Date;

@Data // Getter, Setter 자동 생성
public class NewsDto {
    private Long id;
    private String title;
    private String link;
    private String summary;
    private Date createdAt;
}