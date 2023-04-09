package com.capstone.aiconan.service;

import com.capstone.aiconan.repository.DetectionRepository;
import com.capstone.aiconan.repository.TypesRepository;
import com.capstone.aiconan.response.DetectionResponse;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import javax.transaction.Transactional;

import static com.capstone.aiconan.domain.TypeOfAttack.DOS;
import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@Transactional
class DetectionServiceTest {

    @Autowired
    DetectionService detectionService;

    @Autowired
    DetectionRepository detectionRepository;

    @Autowired
    TypesRepository typesRepository;

    @Test
    @DisplayName("공격 패킷 저장 테스트")
    void recordAbnormalPackets() throws Exception {
        DetectionResponse flaskResponse = DetectionResponse.builder()
                .CANNetId("123")
                .DLC("123")
                .typeOfAttack(DOS)
                .build();

        detectionService.recordAbnormalPackets(flaskResponse);

        assertThat(detectionRepository.count()).isEqualTo(1);
    }


}