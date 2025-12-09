package com.mylab.finance.controller;

import com.mylab.finance.dto.FinanceDto;
import com.mylab.finance.service.FinancialService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/finance")
@RequiredArgsConstructor
public class FinanceController {

    private final FinancialService financialService;

    // 대량 데이터 수신 (POST /api/finance/bulk)
    @PostMapping("/bulk")
    public String saveBulkData(@RequestBody List<FinanceDto> financeDtoList) {
        financialService.saveBulkData(financeDtoList);
        return "✅ " + financeDtoList.size() + "건 저장 성공";
    }
}
