package com.mylab.finance.mapper;

import com.mylab.finance.dto.FinanceDto;
import org.apache.ibatis.annotations.Mapper;
import java.util.List;

@Mapper
public interface FinanceMapper {
    // 벌크 단위로 Insert
    void insertBulkFinanceData(List<FinanceDto> financeList);
}
