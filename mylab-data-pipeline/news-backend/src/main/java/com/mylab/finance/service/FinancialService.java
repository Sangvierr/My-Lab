package com.mylab.finance.service;

import com.mylab.finance.dto.FinanceDto;
import com.mylab.finance.mapper.FinanceMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;

@Service
@RequiredArgsConstructor
public class FinancialService {
    private final FinanceMapper financeMapper;

    @Transactional
    public void saveBulkData(List<FinanceDto> financeDtoList) {
        if (financeDtoList == null || financeDtoList.isEmpty()) {
            return; // 저장할 데이터가 없으면 종료
        }
        System.out.println("💰 [Finance] " + financeDtoList.size() + "건의 데이터 저장 시작...");
        financeMapper.insertBulkFinanceData(financeDtoList);
        System.out.println("✅ [Finance] 저장 완료!");
    }
}
