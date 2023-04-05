package com.capstone.aiconan.response;

import com.capstone.aiconan.domain.TypeOfAttack;
import lombok.Builder;
import lombok.Getter;

/**
 * packet sample
 * Timestamp: 1479121434.854108
 * ID: 0545    000
 * DLC: 8
 * d8 00 00 8a 00 00 00 00
 */
@Getter
public class DetectionResponse {

    private final String CANNetId;
    private final String DLC;
    private final String data;
    private final TypeOfAttack typeOfAttack;

    @Builder
    public DetectionResponse(String CANNetId, String DLC, String data, TypeOfAttack typeOfAttack) {
        this.CANNetId = CANNetId;
        this.DLC = DLC;
        this.data = data;
        this.typeOfAttack = typeOfAttack;
    }
}
