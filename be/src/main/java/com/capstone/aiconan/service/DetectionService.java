package com.capstone.aiconan.service;

import com.capstone.aiconan.domain.Abnormal;
import com.capstone.aiconan.domain.AttackType;
import com.capstone.aiconan.domain.TypeOfAttack;
import com.capstone.aiconan.repository.DetectionRepository;
import com.capstone.aiconan.repository.TypesRepository;
import com.capstone.aiconan.response.DetectionResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;


@Slf4j
@Transactional(readOnly = true)
@Service
@RequiredArgsConstructor
public class DetectionService {

    private final DetectionRepository detectionRepository;
    private final TypesRepository typesRepository;

    @Transactional
    public void recordAbnormalPackets(DetectionResponse flaskResponse) {
        log.info(">> recording abnormal packets to server");

        TypeOfAttack typeOfAttack = TypeOfAttack.valueOf(flaskResponse.getTypeOfAttack().toString());


        AttackType attackType = typesRepository.findByName(TypeOfAttack.DOS)
                .orElseThrow(() -> new IllegalArgumentException("해당하는 record 없음"));


        detectionRepository.save(Abnormal.builder()
                .attackType(attackType)
                .build());


    }
}
