package com.mylab.finance.dto;

import lombok.Data;
import java.util.Date;

@Data
public class FinanceDto {
    private Long id;
    private String corpCode;
    private String corpName;
    private String year;
    private String quarter;

    private Long revenue;           // 매출액
    private Long operatingProfit;   // 영업이익
    private Long netIncome;         // 당기순이익

    private String aiSummary;       // 요약
    private String aiRisk;          // 리스크

    private Date createdAt;
}
